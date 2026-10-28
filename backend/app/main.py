"""Nexo ERP — API principal (FastAPI).

Execução:
    uvicorn app.main:app --reload
Documentação interativa: http://localhost:8000/docs
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .models import *  # noqa: F401,F403 — garante o registro dos modelos
from .routers import (audit, auth, clients, orders, products, reports, sales,
                      stock, suppliers, users)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Nexo ERP API",
    version="1.0.0",
    description="Mini-ERP de Estoque e Vendas — autenticação JWT, RBAC, "
                "estoque com histórico imutável, vendas transacionais e auditoria.",
)

# CORS_ORIGINS="https://meu-frontend.onrender.com,https://outro.com" no .env
# Se não definido, libera tudo (bom para testar; restrinja em produção).
_cors_env = os.getenv("CORS_ORIGINS", "*")
_origins = ["*"] if _cors_env.strip() == "*" else [o.strip() for o in _cors_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, products, stock, sales, clients, suppliers, orders, reports,
          users, audit):
    app.include_router(r.router)


@app.get("/")
def root():
    return {"sistema": "Nexo ERP API", "docs": "/docs", "versao": "1.0.0"}
