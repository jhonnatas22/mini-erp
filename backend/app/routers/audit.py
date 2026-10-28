"""Auditoria — trilha de ações (somente admin)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import AuditLog, User
from ..schemas import AuditOut

router = APIRouter(prefix="/auditoria", tags=["Auditoria"])


@router.get("", response_model=list[AuditOut])
def listar(limite: int = 200, db: Session = Depends(get_db),
           user: User = Depends(require_role("admin", "superadmin"))):
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .limit(min(limite, 1000))
        .all()
    )
    return [
        AuditOut(
            id=l.id, usuario_nome=l.usuario.nome if l.usuario else None,
            acao=l.acao, entidade=l.entidade, entidade_id=l.entidade_id,
            detalhe=l.detalhe, created_at=l.created_at,
        )
        for l in logs
    ]
