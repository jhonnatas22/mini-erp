"""Usuários — gestão de acessos (somente superadmin)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import AuditLog, User
from ..schemas import UserCreate, UserOut, UserUpdate
from ..security import hash_password

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.get("", response_model=list[UserOut])
def listar(db: Session = Depends(get_db),
           user: User = Depends(require_role("superadmin"))):
    return db.query(User).order_by(User.nome).all()


@router.post("", response_model=UserOut, status_code=201)
def criar(dados: UserCreate, db: Session = Depends(get_db),
          user: User = Depends(require_role("superadmin"))):
    if db.query(User).filter(User.email == dados.email).first():
        raise HTTPException(409, "Já existe um usuário com este e-mail.")
    novo = User(nome=dados.nome, email=dados.email,
                senha_hash=hash_password(dados.senha), role=dados.role)
    db.add(novo)
    db.add(AuditLog(usuario_id=user.id, acao="CRIAR_USUARIO", entidade="usuarios",
                    detalhe=f"Usuário '{novo.email}' com perfil '{novo.role}'"))
    db.commit()
    db.refresh(novo)
    return novo


@router.put("/{usuario_id}", response_model=UserOut)
def atualizar(usuario_id: int, dados: UserUpdate, db: Session = Depends(get_db),
              user: User = Depends(require_role("superadmin"))):
    alvo = db.get(User, usuario_id)
    if not alvo:
        raise HTTPException(404, "Usuário não encontrado.")
    if alvo.id == user.id and dados.ativo is False:
        raise HTTPException(400, "Você não pode desativar a si mesmo.")
    if dados.role:
        alvo.role = dados.role
    if dados.ativo is not None:
        alvo.ativo = dados.ativo
    db.add(AuditLog(usuario_id=user.id, acao="ALTERAR_PERMISSAO", entidade="usuarios",
                    entidade_id=alvo.id,
                    detalhe=f"'{alvo.email}' → role={alvo.role}, ativo={alvo.ativo}"))
    db.commit()
    db.refresh(alvo)
    return alvo
