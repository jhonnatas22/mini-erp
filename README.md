# Nexo ERP — Backend (Mini-ERP de Estoque e Vendas)

API REST desenvolvida em **FastAPI + SQLAlchemy** com autenticação JWT, controle de
acesso por perfil (RBAC), estoque com histórico imutável, vendas transacionais,
pedidos/orçamentos, relatórios e trilha de auditoria.

## Requisitos

- Python 3.10+

## Instalação e execução

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # ajuste SECRET_KEY em produção
python -m app.seed              # cria o banco com dados de demonstração
uvicorn app.main:app --reload   # sobe em http://localhost:8000
```

Documentação interativa (Swagger): **http://localhost:8000/docs**

## Perfis de acesso (RBAC)

| Perfil | Acesso principal |
|---|---|
| `superadmin` | Tudo, inclusive gestão de usuários e permissões |
| `admin` | Produtos, estoque (ajustes), vendas, cancelamentos, relatórios, auditoria |
| `funcionario` | Registrar vendas, consultar produtos/estoque, criar clientes, converter pedidos |
| `cliente` | Vitrine de produtos, criar/cancelar seus pedidos |

## Usuários de demonstração (senha: `demo123`)

- `super@nexoerp.com` — superadmin
- `admin@nexoerp.com` — administrador
- `caixa@nexoerp.com` — funcionário (caixa)
- `cliente@nexoerp.com` — cliente

## Regras de negócio implementadas

1. Venda bloqueada quando a quantidade excede o estoque disponível.
2. Produto inativo não pode ser vendido nem movimentado.
3. Preço de venda nunca negativo (validação no schema e no cadastro).
4. Venda cancelada não pode ser cancelada novamente (HTTP 409).
5. Somente `admin`/`superadmin` ajustam estoque manualmente.
6. Toda alteração de estoque gera movimentação com motivo e responsável.
7. Venda nunca é excluída — apenas cancelada, com devolução automática ao estoque.
8. Produto/fornecedor com histórico nunca é apagado — é inativado.
9. Venda é transacional: valida tudo antes de gravar; erro desfaz a operação.

## Endpoints principais

```
POST /auth/login                     → JWT (todos)
GET  /produtos?busca=                → lista com busca (código de barras incluso)
POST /produtos                       → criar (admin)
POST /produtos/{id}/lotes            → lote + validade (admin)
GET  /estoque                        → posição de estoque
GET  /estoque/movimentacoes          → histórico imutável
POST /estoque/entrada | /saida       → ajuste manual (admin)
POST /vendas                         → venda transacional (funcionario/admin)
POST /vendas/{id}/cancelar           → cancela e devolve estoque (admin)
GET  /clientes / POST / PUT / DELETE
GET  /clientes/{id}/historico        → compras, total gasto, última compra
GET  /fornecedores / POST / PUT / DELETE
POST /pedidos                        → cliente cria orçamento
POST /pedidos/{id}/converter         → converte em venda (equipe)
GET  /relatorios/vendas              → faturamento, ticket médio
GET  /relatorios/estoque             → valor estimado, baixo, zerado
GET  /relatorios/produtos-mais-vendidos
GET  /auditoria                      → trilha completa (admin)
GET  /usuarios / POST / PUT          → gestão de acessos (superadmin)
```

## Banco de dados

SQLite por padrão (`nexo.db`). Para PostgreSQL/MySQL, ajuste `DATABASE_URL` no `.env`:

```
DATABASE_URL=postgresql://usuario:senha@localhost:5432/nexo
```

## Estrutura

```
backend/
├── app/
│   ├── main.py          # app FastAPI + registro de rotas
│   ├── database.py      # engine/sessão SQLAlchemy
│   ├── models.py        # entidades (usuários, produtos, vendas, lotes, auditoria...)
│   ├── schemas.py       # validação Pydantic
│   ├── security.py      # bcrypt + JWT
│   ├── deps.py          # get_current_user + require_role (RBAC)
│   ├── seed.py          # dados de demonstração
│   └── routers/         # auth, produtos, estoque, vendas, clientes,
│                        # fornecedores, pedidos, relatórios, usuários, auditoria
├── requirements.txt
└── .env.example
```
