"""Pedidos/Orçamentos — cliente cria, equipe converte em venda com validação de estoque."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import (AuditLog, Client, Order, OrderItem, Product, Sale, SaleItem,
                      StockMovement, User)
from ..schemas import OrderCreate, OrderItemOut, OrderOut

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


def _vincular_cliente(db: Session, user: User) -> Client:
    """Localiza (ou cria) o cadastro de cliente vinculado ao usuário logado."""
    cliente = db.query(Client).filter(Client.usuario_id == user.id).first()
    if not cliente:
        cliente = Client(usuario_id=user.id, nome=user.nome, email=user.email)
        db.add(cliente)
        db.flush()
    return cliente


def to_out(p: Order) -> OrderOut:
    return OrderOut(
        id=p.id, cliente_id=p.cliente_id, cliente_nome=p.cliente.nome,
        status=p.status, data=p.data, venda_id=p.venda_id,
        itens=[OrderItemOut(produto_id=i.produto_id, produto_nome=i.produto.nome,
                            quantidade=i.quantidade, preco_unitario=i.preco_unitario)
               for i in p.itens],
    )


@router.post("", response_model=OrderOut, status_code=201)
def criar(dados: OrderCreate, db: Session = Depends(get_db),
          user: User = Depends(require_role("cliente", "admin", "superadmin", "funcionario"))):
    processados = []
    for item in dados.itens:
        prod = db.get(Product, item.produto_id)
        if not prod:
            raise HTTPException(404, f"Produto {item.produto_id} não encontrado.")
        if prod.status != "ATIVO":
            raise HTTPException(400, f"Produto '{prod.nome}' está indisponível.")
        processados.append((prod, item.quantidade))

    cliente = _vincular_cliente(db, user) if user.role == "cliente" else None
    pedido = Order(cliente_id=cliente.id if cliente else _vincular_cliente(db, user).id)
    db.add(pedido)
    db.flush()
    for prod, qtd in processados:
        db.add(OrderItem(pedido_id=pedido.id, produto_id=prod.id, quantidade=qtd,
                         preco_unitario=prod.preco_venda))
    db.add(AuditLog(usuario_id=user.id, acao="CRIAR_PEDIDO", entidade="pedidos",
                    entidade_id=pedido.id, detalhe=f"Pedido #{pedido.id} criado"))
    db.commit()
    db.refresh(pedido)
    return to_out(pedido)


@router.get("", response_model=list[OrderOut])
def listar(db: Session = Depends(get_db),
           user: User = Depends(require_role("cliente", "admin", "superadmin", "funcionario"))):
    q = db.query(Order).order_by(Order.id.desc())
    if user.role == "cliente":
        cliente = db.query(Client).filter(Client.usuario_id == user.id).first()
        q = q.filter(Order.cliente_id == cliente.id) if cliente else q.filter(Order.id == -1)
    return [to_out(p) for p in q.limit(200).all()]


@router.post("/{pedido_id}/converter", response_model=OrderOut)
def converter(pedido_id: int, forma_pagamento: str = "A combinar",
              db: Session = Depends(get_db),
              user: User = Depends(require_role("admin", "superadmin", "funcionario"))):
    """Converte o pedido em venda: valida estoque, baixa e movimenta (transação única)."""
    pedido = db.get(Order, pedido_id)
    if not pedido:
        raise HTTPException(404, "Pedido não encontrado.")
    if pedido.status != "ABERTO":
        raise HTTPException(409, f"Pedido já está com status '{pedido.status}'.")

    processados = []
    subtotal = 0.0
    for item in pedido.itens:
        prod = db.get(Product, item.produto_id)
        if prod.status != "ATIVO":
            raise HTTPException(400, f"Produto '{prod.nome}' está inativo.")
        if prod.estoque_atual < item.quantidade:
            raise HTTPException(400, f"Estoque insuficiente para '{prod.nome}'.")
        valor = round(item.preco_unitario * item.quantidade, 2)
        subtotal += valor
        processados.append((prod, item.quantidade, valor))

    venda = Sale(cliente_id=pedido.cliente_id, usuario_id=user.id,
                 subtotal=round(subtotal, 2), desconto=0, total=round(subtotal, 2),
                 status="ATIVA", forma_pagamento=forma_pagamento)
    db.add(venda)
    db.flush()
    for prod, qtd, valor in processados:
        db.add(SaleItem(venda_id=venda.id, produto_id=prod.id, quantidade=qtd,
                        preco_unitario=prod.preco_venda, subtotal=valor))
        prod.estoque_atual -= qtd
        db.add(StockMovement(produto_id=prod.id, tipo="SAIDA", quantidade=qtd,
                             motivo=f"Venda #{venda.id} (pedido #{pedido.id})",
                             usuario_id=user.id))

    pedido.status = "CONVERTIDO"
    pedido.venda_id = venda.id
    db.add(AuditLog(usuario_id=user.id, acao="CONVERTER_PEDIDO", entidade="pedidos",
                    entidade_id=pedido.id,
                    detalhe=f"Pedido #{pedido.id} convertido na venda #{venda.id}"))
    db.commit()
    db.refresh(pedido)
    return to_out(pedido)


@router.post("/{pedido_id}/cancelar", response_model=OrderOut)
def cancelar(pedido_id: int, db: Session = Depends(get_db),
             user: User = Depends(require_role("cliente", "admin", "superadmin"))):
    pedido = db.get(Order, pedido_id)
    if not pedido:
        raise HTTPException(404, "Pedido não encontrado.")
    if pedido.status != "ABERTO":
        raise HTTPException(409, "Somente pedidos abertos podem ser cancelados.")
    if user.role == "cliente":
        cliente = db.query(Client).filter(Client.usuario_id == user.id).first()
        if not cliente or pedido.cliente_id != cliente.id:
            raise HTTPException(403, "Você só pode cancelar os seus próprios pedidos.")
    pedido.status = "CANCELADO"
    db.add(AuditLog(usuario_id=user.id, acao="CANCELAR_PEDIDO", entidade="pedidos",
                    entidade_id=pedido.id, detalhe=f"Pedido #{pedido.id} cancelado"))
    db.commit()
    db.refresh(pedido)
    return to_out(pedido)
