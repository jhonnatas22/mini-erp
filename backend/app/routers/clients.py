"""Clientes — CRUD e histórico de compras."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import AuditLog, Client, Sale, User
from ..schemas import ClientHistory, ClientIn, ClientOut

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("", response_model=list[ClientOut])
def listar(busca: str = "", db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    q = db.query(Client)
    if busca:
        q = q.filter(Client.nome.like(f"%{busca}%"))
    return q.order_by(Client.nome).all()


@router.post("", response_model=ClientOut, status_code=201)
def criar(dados: ClientIn, db: Session = Depends(get_db),
          user: User = Depends(get_current_user)):
    c = Client(**dados.model_dump())
    db.add(c)
    db.add(AuditLog(usuario_id=user.id, acao="CRIAR_CLIENTE", entidade="clientes",
                    detalhe=f"Cliente '{c.nome}' criado"))
    db.commit()
    db.refresh(c)
    return c


@router.get("/{cliente_id}", response_model=ClientOut)
def detalhe(cliente_id: int, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    c = db.get(Client, cliente_id)
    if not c:
        raise HTTPException(404, "Cliente não encontrado.")
    return c


@router.put("/{cliente_id}", response_model=ClientOut)
def atualizar(cliente_id: int, dados: ClientIn, db: Session = Depends(get_db),
              user: User = Depends(require_role("admin", "superadmin", "funcionario"))):
    c = db.get(Client, cliente_id)
    if not c:
        raise HTTPException(404, "Cliente não encontrado.")
    for k, v in dados.model_dump().items():
        setattr(c, k, v)
    db.add(AuditLog(usuario_id=user.id, acao="EDITAR_CLIENTE", entidade="clientes",
                    entidade_id=c.id, detalhe=f"Cliente '{c.nome}' atualizado"))
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{cliente_id}", status_code=204)
def excluir(cliente_id: int, db: Session = Depends(get_db),
            user: User = Depends(require_role("admin", "superadmin"))):
    c = db.get(Client, cliente_id)
    if not c:
        raise HTTPException(404, "Cliente não encontrado.")
    c.ativo = False  # preserva histórico de vendas
    db.add(AuditLog(usuario_id=user.id, acao="INATIVAR_CLIENTE", entidade="clientes",
                    entidade_id=c.id, detalhe=f"Cliente '{c.nome}' inativado"))
    db.commit()


@router.get("/{cliente_id}/historico", response_model=ClientHistory)
def historico(cliente_id: int, db: Session = Depends(get_db),
              user: User = Depends(require_role("admin", "superadmin", "funcionario"))):
    c = db.get(Client, cliente_id)
    if not c:
        raise HTTPException(404, "Cliente não encontrado.")
    vendas = (
        db.query(Sale)
        .filter(Sale.cliente_id == c.id, Sale.status == "ATIVA")
        .all()
    )
    return ClientHistory(
        compras=len(vendas),
        total_gasto=round(sum(v.total for v in vendas), 2),
        ultima_compra=max((v.data for v in vendas), default=None),
    )
