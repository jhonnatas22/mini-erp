"""Produtos — CRUD com regras de negócio e leitura por código de barras."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import AuditLog, Category, Lot, Product
from ..schemas import LotIn, LotOut, ProductIn, ProductOut, UserOut

router = APIRouter(prefix="/produtos", tags=["Produtos"])


def to_out(p: Product) -> ProductOut:
    return ProductOut(
        id=p.id, nome=p.nome, sku=p.sku, codigo_barras=p.codigo_barras,
        marca=p.marca, categoria_nome=p.categoria.nome if p.categoria else None,
        fornecedor_nome=p.fornecedor.nome_fantasia if p.fornecedor else None,
        preco_custo=p.preco_custo, preco_venda=p.preco_venda,
        estoque_atual=p.estoque_atual, estoque_minimo=p.estoque_minimo,
        unidade=p.unidade, status=p.status,
    )


def validar_regras(db: Session, dados: ProductIn, produto_id: int | None = None):
    """Regras: categoria existe, SKU único, preço de venda >= 0."""
    if not db.get(Category, dados.categoria_id):
        raise HTTPException(404, "Categoria não encontrada.")
    if dados.preco_venda < 0:
        raise HTTPException(422, "Preço de venda não pode ser negativo.")
    q = db.query(Product).filter(Product.sku == dados.sku)
    if produto_id:
        q = q.filter(Product.id != produto_id)
    if q.first():
        raise HTTPException(409, f"Já existe um produto com o SKU '{dados.sku}'.")


@router.get("", response_model=list[ProductOut])
def listar(
    busca: str = "",
    categoria_id: int = 0,
    db: Session = Depends(get_db),
    user: UserOut = Depends(get_current_user),
):
    q = db.query(Product)
    if busca:
        like = f"%{busca}%"
        q = q.filter(
            Product.nome.like(like)
            | Product.sku.like(like)
            | Product.codigo_barras.like(like)
        )
    if categoria_id:
        q = q.filter(Product.categoria_id == categoria_id)
    return [to_out(p) for p in q.order_by(Product.nome).all()]


@router.get("/{produto_id}", response_model=ProductOut)
def detalhe(produto_id: int, db: Session = Depends(get_db),
            user: UserOut = Depends(get_current_user)):
    p = db.get(Product, produto_id)
    if not p:
        raise HTTPException(404, "Produto não encontrado.")
    return to_out(p)


@router.post("", response_model=ProductOut, status_code=201)
def criar(dados: ProductIn, db: Session = Depends(get_db),
          user=Depends(require_role("admin", "superadmin"))):
    validar_regras(db, dados)
    p = Product(**dados.model_dump())
    db.add(p)
    db.add(AuditLog(usuario_id=user.id, acao="CRIAR_PRODUTO", entidade="produtos",
                    detalhe=f"Produto '{p.nome}' criado"))
    db.commit()
    db.refresh(p)
    return to_out(p)


@router.put("/{produto_id}", response_model=ProductOut)
def atualizar(produto_id: int, dados: ProductIn, db: Session = Depends(get_db),
              user=Depends(require_role("admin", "superadmin"))):
    p = db.get(Product, produto_id)
    if not p:
        raise HTTPException(404, "Produto não encontrado.")
    validar_regras(db, dados, produto_id)
    antes = f"custo={p.preco_custo}, venda={p.preco_venda}, status={p.status}"
    for k, v in dados.model_dump().items():
        setattr(p, k, v)
    db.add(AuditLog(usuario_id=user.id, acao="EDITAR_PRODUTO", entidade="produtos",
                    entidade_id=p.id, detalhe=f"'{p.nome}' — antes: {antes}"))
    db.commit()
    db.refresh(p)
    return to_out(p)


@router.delete("/{produto_id}", status_code=204)
def excluir(produto_id: int, db: Session = Depends(get_db),
            user=Depends(require_role("admin", "superadmin"))):
    """Nunca apaga produto com histórico: inativa (preserva integridade e auditoria)."""
    p = db.get(Product, produto_id)
    if not p:
        raise HTTPException(404, "Produto não encontrado.")
    if p.movimentacoes:
        p.status = "INATIVO"
        acao = "INATIVAR_PRODUTO"
    else:
        db.delete(p)
        acao = "EXCLUIR_PRODUTO"
    db.add(AuditLog(usuario_id=user.id, acao=acao, entidade="produtos",
                    entidade_id=p.id, detalhe=f"Produto '{p.nome}'"))
    db.commit()


# ---------- Lotes e validade ----------
@router.get("/{produto_id}/lotes", response_model=list[LotOut])
def lotes(produto_id: int, db: Session = Depends(get_db),
          user: UserOut = Depends(get_current_user)):
    p = db.get(Product, produto_id)
    if not p:
        raise HTTPException(404, "Produto não encontrado.")
    return p.lotes


@router.post("/{produto_id}/lotes", response_model=LotOut, status_code=201)
def criar_lote(produto_id: int, dados: LotIn, db: Session = Depends(get_db),
               user=Depends(require_role("admin", "superadmin"))):
    p = db.get(Product, produto_id)
    if not p:
        raise HTTPException(404, "Produto não encontrado.")
    lote = Lot(produto_id=produto_id, **dados.model_dump())
    db.add(lote)
    db.add(AuditLog(usuario_id=user.id, acao="CRIAR_LOTE", entidade="lotes",
                    detalhe=f"Lote {lote.numero} do produto '{p.nome}'"))
    db.commit()
    db.refresh(lote)
    return lote
