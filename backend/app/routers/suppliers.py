"""Fornecedores — CRUD."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import AuditLog, Supplier, User
from ..schemas import SupplierIn, SupplierOut

router = APIRouter(prefix="/fornecedores", tags=["Fornecedores"])


@router.get("", response_model=list[SupplierOut])
def listar(db: Session = Depends(get_db), user: User = Depends(require_role("admin", "superadmin", "funcionario"))):
    return db.query(Supplier).order_by(Supplier.razao_social).all()


@router.post("", response_model=SupplierOut, status_code=201)
def criar(dados: SupplierIn, db: Session = Depends(get_db),
          user: User = Depends(require_role("admin", "superadmin"))):
    f = Supplier(**dados.model_dump())
    db.add(f)
    db.add(AuditLog(usuario_id=user.id, acao="CRIAR_FORNECEDOR", entidade="fornecedores",
                    detalhe=f"Fornecedor '{f.razao_social}' criado"))
    db.commit()
    db.refresh(f)
    return f


@router.put("/{fornecedor_id}", response_model=SupplierOut)
def atualizar(fornecedor_id: int, dados: SupplierIn, db: Session = Depends(get_db),
              user: User = Depends(require_role("admin", "superadmin"))):
    f = db.get(Supplier, fornecedor_id)
    if not f:
        raise HTTPException(404, "Fornecedor não encontrado.")
    for k, v in dados.model_dump().items():
        setattr(f, k, v)
    db.add(AuditLog(usuario_id=user.id, acao="EDITAR_FORNECEDOR", entidade="fornecedores",
                    entidade_id=f.id, detalhe=f"'{f.razao_social}' atualizado"))
    db.commit()
    db.refresh(f)
    return f


@router.delete("/{fornecedor_id}", status_code=204)
def excluir(fornecedor_id: int, db: Session = Depends(get_db),
            user: User = Depends(require_role("admin", "superadmin"))):
    f = db.get(Supplier, fornecedor_id)
    if not f:
        raise HTTPException(404, "Fornecedor não encontrado.")
    if f.produtos:
        f.ativo = False
        acao = "INATIVAR_FORNECEDOR"
    else:
        db.delete(f)
        acao = "EXCLUIR_FORNECEDOR"
    db.add(AuditLog(usuario_id=user.id, acao=acao, entidade="fornecedores",
                    entidade_id=f.id, detalhe=f"'{f.razao_social}'"))
    db.commit()
