"""Vendas — criação transacional, baixa automática de estoque e cancelamento com devolução."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import AuditLog, Client, Product, Sale, SaleItem, StockMovement
from ..schemas import SaleCreate, SaleItemOut, SaleOut

router = APIRouter(prefix="/vendas", tags=["Vendas"])


def to_out(v: Sale) -> SaleOut:
    return SaleOut(
        id=v.id, cliente_id=v.cliente_id,
        cliente_nome=v.cliente.nome if v.cliente else None,
        usuario_nome=v.usuario.nome, data=v.data, subtotal=v.subtotal,
        desconto=v.desconto, total=v.total, status=v.status,
        forma_pagamento=v.forma_pagamento,
        itens=[SaleItemOut(produto_id=i.produto_id, produto_nome=i.produto.nome,
                           quantidade=i.quantidade, preco_unitario=i.preco_unitario,
                           subtotal=i.subtotal) for i in v.itens],
    )


@router.post("", response_model=SaleOut, status_code=201)
def criar_venda(dados: SaleCreate, db: Session = Depends(get_db),
                user=Depends(require_role("admin", "superadmin", "funcionario"))):
    if dados.cliente_id and not db.get(Client, dados.cliente_id):
        raise HTTPException(404, "Cliente não encontrado.")

    # 1) Valida TODAS as regras antes de mexer no banco (nada pela metade)
    processados = []
    subtotal = 0.0
    for item in dados.itens:
        prod = db.get(Product, item.produto_id)
        if not prod:
            raise HTTPException(404, f"Produto {item.produto_id} não encontrado.")
        if prod.status != "ATIVO":
            raise HTTPException(400, f"Produto '{prod.nome}' está inativo e não pode ser vendido.")
        if prod.preco_venda < 0:
            raise HTTPException(400, f"Preço de venda inválido para '{prod.nome}'.")
        if prod.estoque_atual < item.quantidade:
            raise HTTPException(
                400,
                f"Estoque insuficiente para '{prod.nome}' "
                f"(disponível: {prod.estoque_atual}).",
            )
        valor = round(prod.preco_venda * item.quantidade, 2)
        subtotal += valor
        processados.append((prod, item.quantidade, valor))

    total = round(subtotal - dados.desconto, 2)
    if total < 0:
        raise HTTPException(400, "Desconto não pode ser maior que o subtotal.")

    # 2) Executa tudo em uma única transação
    venda = Sale(
        cliente_id=dados.cliente_id, usuario_id=user.id, subtotal=round(subtotal, 2),
        desconto=dados.desconto, total=total, status="ATIVA",
        forma_pagamento=dados.forma_pagamento,
    )
    db.add(venda)
    db.flush()

    for prod, qtd, valor in processados:
        db.add(SaleItem(venda_id=venda.id, produto_id=prod.id, quantidade=qtd,
                        preco_unitario=prod.preco_venda, subtotal=valor))
        prod.estoque_atual -= qtd
        db.add(StockMovement(produto_id=prod.id, tipo="SAIDA", quantidade=qtd,
                             motivo=f"Venda #{venda.id}", usuario_id=user.id))

    db.add(AuditLog(usuario_id=user.id, acao="CRIAR_VENDA", entidade="vendas",
                    entidade_id=venda.id, detalhe=f"Venda #{venda.id} — {total:.2f}"))
    db.commit()
    db.refresh(venda)
    return to_out(venda)


@router.get("", response_model=list[SaleOut])
def listar(status: str = "", db: Session = Depends(get_db),
           user=Depends(require_role("admin", "superadmin", "funcionario"))):
    q = db.query(Sale).order_by(Sale.id.desc())
    if status:
        q = q.filter(Sale.status == status.upper())
    return [to_out(v) for v in q.limit(200).all()]


@router.get("/{venda_id}", response_model=SaleOut)
def detalhe(venda_id: int, db: Session = Depends(get_db),
            user=Depends(require_role("admin", "superadmin", "funcionario"))):
    venda = db.get(Sale, venda_id)
    if not venda:
        raise HTTPException(404, "Venda não encontrada.")
    return to_out(venda)


@router.post("/{venda_id}/cancelar", response_model=SaleOut)
def cancelar(venda_id: int, db: Session = Depends(get_db),
             user=Depends(require_role("admin", "superadmin"))):
    """Somente admin. Nunca apaga: cancela e devolve o estoque (Regras 4 e 7)."""
    venda = db.get(Sale, venda_id)
    if not venda:
        raise HTTPException(404, "Venda não encontrada.")
    if venda.status == "CANCELADA":
        raise HTTPException(409, "Esta venda já está cancelada.")

    for item in venda.itens:
        prod = db.get(Product, item.produto_id)
        if prod:
            prod.estoque_atual += item.quantidade
            db.add(StockMovement(produto_id=prod.id, tipo="ENTRADA",
                                 quantidade=item.quantidade,
                                 motivo=f"Cancelamento venda #{venda.id}",
                                 usuario_id=user.id))

    venda.status = "CANCELADA"
    db.add(AuditLog(usuario_id=user.id, acao="CANCELAR_VENDA", entidade="vendas",
                    entidade_id=venda.id, detalhe=f"Venda #{venda.id} cancelada"))
    db.commit()
    db.refresh(venda)
    return to_out(venda)
