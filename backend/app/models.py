"""Modelos do banco de dados — Mini-ERP Nexo."""
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base

# Perfis de acesso (RBAC)
ROLES = ("superadmin", "admin", "funcionario", "cliente")


class User(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    nome = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="funcionario")
    ativo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())

    vendas = relationship("Sale", back_populates="usuario")
    movimentacoes = relationship("StockMovement", back_populates="usuario")


class Category(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True)
    nome = Column(String(80), nullable=False, unique=True)
    descricao = Column(String(255))

    produtos = relationship("Product", back_populates="categoria")


class Supplier(Base):
    __tablename__ = "fornecedores"

    id = Column(Integer, primary_key=True)
    razao_social = Column(String(160), nullable=False)
    nome_fantasia = Column(String(160))
    cnpj = Column(String(20), unique=True)
    telefone = Column(String(20))
    email = Column(String(160))
    endereco = Column(String(255))
    ativo = Column(Boolean, nullable=False, default=True)

    produtos = relationship("Product", back_populates="fornecedor")


class Product(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"), nullable=True)
    nome = Column(String(160), nullable=False)
    descricao = Column(Text)
    sku = Column(String(40), unique=True, nullable=False)
    codigo_barras = Column(String(20), unique=True, nullable=True)
    marca = Column(String(80))
    preco_custo = Column(Float, nullable=False, default=0)
    preco_venda = Column(Float, nullable=False, default=0)
    estoque_atual = Column(Integer, nullable=False, default=0)
    estoque_minimo = Column(Integer, nullable=False, default=0)
    unidade = Column(String(10), nullable=False, default="UN")
    status = Column(String(10), nullable=False, default="ATIVO")  # ATIVO / INATIVO
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    categoria = relationship("Category", back_populates="produtos")
    fornecedor = relationship("Supplier", back_populates="produtos")
    movimentacoes = relationship("StockMovement", back_populates="produto")
    lotes = relationship("Lot", back_populates="produto", cascade="all, delete-orphan")


class Lot(Base):
    __tablename__ = "lotes"

    id = Column(Integer, primary_key=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    numero = Column(String(40), nullable=False)
    validade = Column(Date, nullable=True)
    quantidade = Column(Integer, nullable=False, default=0)

    produto = relationship("Product", back_populates="lotes")


class Client(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=True)
    nome = Column(String(160), nullable=False)
    cpf = Column(String(14), unique=True, nullable=True)
    telefone = Column(String(20))
    email = Column(String(160))
    endereco = Column(String(255))
    ativo = Column(Boolean, nullable=False, default=True)

    vendas = relationship("Sale", back_populates="cliente")


class StockMovement(Base):
    __tablename__ = "movimentacoes_estoque"

    id = Column(Integer, primary_key=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    lote_id = Column(Integer, ForeignKey("lotes.id"), nullable=True)
    tipo = Column(String(10), nullable=False)  # ENTRADA / SAIDA
    quantidade = Column(Integer, nullable=False)
    motivo = Column(String(120), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    produto = relationship("Product", back_populates="movimentacoes")
    usuario = relationship("User", back_populates="movimentacoes")


class Sale(Base):
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    data = Column(DateTime, server_default=func.now())
    subtotal = Column(Float, nullable=False, default=0)
    desconto = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False, default=0)
    status = Column(String(10), nullable=False, default="ATIVA")  # ATIVA / CANCELADA
    forma_pagamento = Column(String(30), nullable=False)

    cliente = relationship("Client", back_populates="vendas")
    usuario = relationship("User", back_populates="vendas")
    itens = relationship(
        "SaleItem", back_populates="venda", cascade="all, delete-orphan"
    )


class SaleItem(Base):
    __tablename__ = "itens_venda"

    id = Column(Integer, primary_key=True)
    venda_id = Column(Integer, ForeignKey("vendas.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    venda = relationship("Sale", back_populates="itens")
    produto = relationship("Product")


class Order(Base):
    """Pedido/orçamento — criado pelo cliente, convertido em venda pela equipe."""

    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    status = Column(String(12), nullable=False, default="ABERTO")  # ABERTO / CONVERTIDO / CANCELADO
    data = Column(DateTime, server_default=func.now())
    venda_id = Column(Integer, ForeignKey("vendas.id"), nullable=True)

    cliente = relationship("Client")
    itens = relationship(
        "OrderItem", back_populates="pedido", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "itens_pedido"

    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)

    pedido = relationship("Order", back_populates="itens")
    produto = relationship("Product")


class AuditLog(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    acao = Column(String(60), nullable=False)
    entidade = Column(String(60))
    entidade_id = Column(Integer, nullable=True)
    detalhe = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    usuario = relationship("User")
