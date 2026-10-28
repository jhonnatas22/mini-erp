"""Estoque — consulta e movimentações com histórico imutável."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import AuditLog, Lot, Product, StockMovement
from ..schemas import MovementIn, MovementOut, ProductOut
from .products import to_out

router = APIRouter(tags=["Estoque"])


@router.get("/estoque", response_model=list[ProductOut])
def estoque(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return [to_out(p) for p in db.query(Product).order_by(Product.nome).all()]


def to_movement_out(m: StockMovement) -> MovementOut:
    return MovementOut(
        id=m.id, produto_id=m.produto_id, produto_nome=m.produto.nome,
        tipo=m.tipo, quantidade=m.quantidade, motivo=m.motivo,
        usuario_nome=m.usuario.nome, created_at=m.created_at,
    )


@router.get("/estoque/movimentacoes", response_model=list[MovementOut])
def movimentacoes(db: Session = Depends(get_db), user=Depends(get_current_user)):
    movs = (
        db.query(StockMovement)
        .order_by(StockMovement.id.desc())
        .limit(300)
        .all()
    )
    return [to_movement_out(m) for m in movs]


def _aplicar(db: Session, dados: MovementIn, tipo: str, user) -> MovementOut:
    prod = db.get(Product, dados.produto_id)
    if not prod:
        raise HTTPException(404, "Produto não encontrado.")
    if prod.status != "ATIVO":
        raise HTTPException(400, f"Produto '{prod.nome}' está inativo.")

    lote = None
    if dados.lote_id:
        lote = db.get(Lot, dados.lote_id)
        if not lote or lote.produto_id != prod.id:
            raise HTTPException(404, "Lote não encontrado para este produto.")

    if tipo == "SAIDA" and prod.estoque_atual < dados.quantidade:
        raise HTTPException(
            400,
            f"Estoque insuficiente para '{prod.nome}' "
            f"(disponível: {prod.estoque_atual}).",
        )

    prod.estoque_atual += dados.quantidade if tipo == "ENTRADA" else -dados.quantidade
    mov = StockMovement(
        produto_id=prod.id, lote_id=dados.lote_id, tipo=tipo,
        quantidade=dados.quantidade, motivo=dados.motivo, usuario_id=user.id,
    )
    db.add(mov)
    db.add(AuditLog(usuario_id=user.id, acao=f"{tipo}_ESTOQUE",
                    entidade="movimentacoes", entidade_id=prod.id,
                    detalhe=f"{tipo} {dados.quantidade} un. de '{prod.nome}' — {dados.motivo}"))
    db.commit()
    db.refresh(mov)
    return to_movement_out(mov)


@router.post("/estoque/entrada", response_model=MovementOut, status_code=201)
def entrada(dados: MovementIn, db: Session = Depends(get_db),
            user=Depends(require_role("admin", "superadmin"))):
    """Ajuste/entrada manual: somente admin (Regra 5)."""
    return _aplicar(db, dados, "ENTRADA", user)


@router.post("/estoque/saida", response_model=MovementOut, status_code=201)
def saida(dados: MovementIn, db: Session = Depends(get_db),
          user=Depends(require_role("admin", "superadmin"))):
    return _aplicar(db, dados, "SAIDA", user)
