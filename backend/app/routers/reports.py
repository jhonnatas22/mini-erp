"""Relatórios — vendas, estoque, top produtos, movimentações (somente admin)."""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import Product, Sale, SaleItem, StockMovement, User
from ..schemas import (MovementOut, ProductOut, ReportEstoque, ReportVendas,
                       TopProduct)
from .products import to_out
from .stock import to_movement_out

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])
ADMIN = ("admin", "superadmin")


@router.get("/vendas", response_model=ReportVendas)
def rel_vendas(inicio: datetime = None, fim: datetime = None,
               db: Session = Depends(get_db), user: User = Depends(require_role(*ADMIN))):
    q = db.query(Sale).filter(Sale.status == "ATIVA")
    if inicio:
        q = q.filter(Sale.data >= inicio)
    if fim:
        q = q.filter(Sale.data <= fim)
    vendas = q.all()
    fat = round(sum(v.total for v in vendas), 2)
    return ReportVendas(
        vendas=len(vendas), faturamento=fat,
        ticket_medio=round(fat / len(vendas), 2) if vendas else 0,
    )


@router.get("/estoque", response_model=ReportEstoque)
def rel_estoque(db: Session = Depends(get_db), user: User = Depends(require_role(*ADMIN))):
    produtos = db.query(Product).all()
    ativos = [p for p in produtos if p.status == "ATIVO"]
    return ReportEstoque(
        produtos=len(ativos),
        unidades=sum(p.estoque_atual for p in produtos),
        valor_estimado=round(sum(p.estoque_atual * p.preco_custo for p in produtos), 2),
        estoque_baixo=len([p for p in ativos if 0 < p.estoque_atual <= p.estoque_minimo]),
        sem_estoque=len([p for p in ativos if p.estoque_atual == 0]),
    )


@router.get("/produtos-mais-vendidos", response_model=list[TopProduct])
def rel_top(db: Session = Depends(get_db), user: User = Depends(require_role(*ADMIN))):
    rows = (
        db.query(SaleItem.produto_id, func.sum(SaleItem.quantidade).label("qtd"))
        .join(Sale, Sale.id == SaleItem.venda_id)
        .filter(Sale.status == "ATIVA")
        .group_by(SaleItem.produto_id)
        .order_by(desc("qtd"))
        .limit(10)
        .all()
    )
    resultado = []
    for produto_id, qtd in rows:
        prod = db.get(Product, produto_id)
        if prod:
            resultado.append(TopProduct(produto=prod.nome, quantidade=int(qtd)))
    return resultado


@router.get("/estoque-baixo", response_model=list[ProductOut])
def rel_baixo(db: Session = Depends(get_db), user: User = Depends(require_role(*ADMIN))):
    prods = (
        db.query(Product)
        .filter(Product.status == "ATIVO", Product.estoque_atual <= Product.estoque_minimo)
        .order_by(Product.estoque_atual)
        .all()
    )
    return [to_out(p) for p in prods]


@router.get("/movimentacoes", response_model=list[MovementOut])
def rel_movs(limite: int = 100, db: Session = Depends(get_db),
             user: User = Depends(require_role(*ADMIN))):
    movs = (
        db.query(StockMovement)
        .order_by(StockMovement.id.desc())
        .limit(min(limite, 500))
        .all()
    )
    return [to_movement_out(m) for m in movs]
