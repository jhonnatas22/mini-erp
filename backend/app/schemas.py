"""Schemas Pydantic — validação de entrada e serialização de saída."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth / Usuários ----------
class LoginInput(BaseModel):
    email: EmailStr
    senha: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    nome: str


class UserOut(BaseModel):
    id: int
    nome: str
    email: EmailStr
    role: str
    ativo: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=6)
    role: str = Field(default="funcionario", pattern="^(superadmin|admin|funcionario|cliente)$")


class UserUpdate(BaseModel):
    role: Optional[str] = Field(default=None, pattern="^(superadmin|admin|funcionario|cliente)$")
    ativo: Optional[bool] = None


# ---------- Categorias ----------
class CategoryIn(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    descricao: Optional[str] = None


class CategoryOut(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------- Fornecedores ----------
class SupplierIn(BaseModel):
    razao_social: str = Field(min_length=2)
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    endereco: Optional[str] = None


class SupplierOut(SupplierIn):
    id: int
    ativo: bool

    model_config = {"from_attributes": True}


# ---------- Produtos ----------
class ProductIn(BaseModel):
    categoria_id: int
    fornecedor_id: Optional[int] = None
    nome: str = Field(min_length=2, max_length=160)
    descricao: Optional[str] = None
    sku: str = Field(min_length=2, max_length=40)
    codigo_barras: Optional[str] = None
    marca: Optional[str] = None
    preco_custo: float = Field(ge=0)
    preco_venda: float = Field(ge=0)
    estoque_minimo: int = Field(default=0, ge=0)
    unidade: str = "UN"
    status: str = Field(default="ATIVO", pattern="^(ATIVO|INATIVO)$")


class ProductOut(BaseModel):
    id: int
    nome: str
    sku: str
    codigo_barras: Optional[str]
    marca: Optional[str]
    categoria_nome: Optional[str]
    fornecedor_nome: Optional[str]
    preco_custo: float
    preco_venda: float
    estoque_atual: int
    estoque_minimo: int
    unidade: str
    status: str


class LotIn(BaseModel):
    numero: str = Field(min_length=1, max_length=40)
    validade: Optional[datetime] = None
    quantidade: int = Field(ge=0)


class LotOut(LotIn):
    id: int
    produto_id: int

    model_config = {"from_attributes": True}


# ---------- Estoque ----------
class MovementIn(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0)
    motivo: str = Field(min_length=2, max_length=120)
    lote_id: Optional[int] = None


class MovementOut(BaseModel):
    id: int
    produto_id: int
    produto_nome: str
    tipo: str
    quantidade: int
    motivo: str
    usuario_nome: str
    created_at: datetime


# ---------- Vendas ----------
class SaleItemIn(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0)


class SaleCreate(BaseModel):
    cliente_id: Optional[int] = None
    forma_pagamento: str = Field(min_length=2, max_length=30)
    desconto: float = Field(default=0, ge=0)
    itens: List[SaleItemIn] = Field(min_length=1)


class SaleItemOut(BaseModel):
    produto_id: int
    produto_nome: str
    quantidade: int
    preco_unitario: float
    subtotal: float


class SaleOut(BaseModel):
    id: int
    cliente_id: Optional[int]
    cliente_nome: Optional[str]
    usuario_nome: str
    data: datetime
    subtotal: float
    desconto: float
    total: float
    status: str
    forma_pagamento: str
    itens: List[SaleItemOut]


# ---------- Clientes ----------
class ClientIn(BaseModel):
    nome: str = Field(min_length=2, max_length=160)
    cpf: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    endereco: Optional[str] = None


class ClientOut(ClientIn):
    id: int
    ativo: bool

    model_config = {"from_attributes": True}


class ClientHistory(BaseModel):
    compras: int
    total_gasto: float
    ultima_compra: Optional[datetime]


# ---------- Pedidos ----------
class OrderItemIn(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0)


class OrderCreate(BaseModel):
    itens: List[OrderItemIn] = Field(min_length=1)


class OrderItemOut(BaseModel):
    produto_id: int
    produto_nome: str
    quantidade: int
    preco_unitario: float


class OrderOut(BaseModel):
    id: int
    cliente_id: int
    cliente_nome: str
    status: str
    data: datetime
    venda_id: Optional[int]
    itens: List[OrderItemOut]


# ---------- Auditoria ----------
class AuditOut(BaseModel):
    id: int
    usuario_nome: Optional[str]
    acao: str
    entidade: Optional[str]
    entidade_id: Optional[int]
    detalhe: Optional[str]
    created_at: datetime


# ---------- Relatórios ----------
class ReportVendas(BaseModel):
    vendas: int
    faturamento: float
    ticket_medio: float


class ReportEstoque(BaseModel):
    produtos: int
    unidades: int
    valor_estimado: float
    estoque_baixo: int
    sem_estoque: int


class TopProduct(BaseModel):
    produto: str
    quantidade: int
