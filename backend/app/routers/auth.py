"""Autenticação — login com JWT."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import AuditLog, User
from ..schemas import LoginInput, Token, UserOut
from ..security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=Token)
def login(dados: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == dados.email).first()
    if not user or not verify_password(dados.senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    if not user.ativo:
        raise HTTPException(status_code=403, detail="Usuário inativo. Contate o administrador.")

    db.add(AuditLog(usuario_id=user.id, acao="LOGIN", entidade="auth",
                    detalhe=f"Login de {user.email}"))
    db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return Token(access_token=token, role=user.role, nome=user.nome)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
