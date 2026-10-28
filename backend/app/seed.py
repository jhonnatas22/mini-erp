"""Popula o banco com dados de demonstração.

Uso:
    python -m app.seed
"""
from datetime import date, timedelta

from .database import Base, SessionLocal, engine
from .models import (Category, Client, Lot, Product, StockMovement, Supplier,
                     User)
from .security import hash_password

DEMO_PASSWORD = "demo123"


def seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Usuários (um de cada perfil)
    superadmin = User(nome="Super Admin", email="super@nexoerp.com",
                      senha_hash=hash_password(DEMO_PASSWORD), role="superadmin")
    admin = User(nome="João Silva", email="admin@nexoerp.com",
                 senha_hash=hash_password(DEMO_PASSWORD), role="admin")
    caixa = User(nome="Carlos Almeida", email="caixa@nexoerp.com",
                 senha_hash=hash_password(DEMO_PASSWORD), role="funcionario")
    cliente_user = User(nome="Maria Oliveira", email="cliente@nexoerp.com",
                        senha_hash=hash_password(DEMO_PASSWORD), role="cliente")
    db.add_all([superadmin, admin, caixa, cliente_user])
    db.flush()

    cliente = Client(usuario_id=cliente_user.id, nome="Maria Oliveira",
                     email="cliente@nexoerp.com", telefone="(11) 90000-0000")

    alimentos = Category(nome="Alimentos", descricao="Mercearia em geral")
    bebidas = Category(nome="Bebidas")
    higiene = Category(nome="Higiene")
    db.add_all([alimentos, bebidas, higiene, cliente])

    fornecedor = Supplier(razao_social="Distribuidora ABC Ltda",
                          nome_fantasia="Distribuidora ABC", cnpj="12.345.678/0001-90",
                          telefone="(11) 4000-0000", email="vendas@abc.com.br")
    db.add(fornecedor)
    db.flush()

    def prod(nome, sku, cb, cat, custo, venda, estoque, minimo, un="UN"):
        p = Product(categoria_id=cat, fornecedor_id=fornecedor.id, nome=nome,
                    sku=sku, codigo_barras=cb, preco_custo=custo, preco_venda=venda,
                    estoque_atual=estoque, estoque_minimo=minimo, unidade=un)
        db.add(p)
        db.flush()
        return p

    arroz = prod("Arroz Tipo 1 — 5kg", "ARZ001", "7891234567890",
                 alimentos.id, 20.00, 28.00, 50, 10)
    prod("Feijão Carioca — 1kg", "FEJ001", "7891234567891",
         alimentos.id, 6.50, 9.80, 2, 10)
    cafe = prod("Café Torrado — 500g", "CAF002", "7891234567892",
                alimentos.id, 12.00, 18.90, 4, 8)
    prod("Refrigerante Cola — 2L", "BEB001", "7891234567893",
         bebidas.id, 7.20, 10.50, 48, 12)
    prod("Sabonete Neutro — 90g", "HIG001", "7891234567894",
         higiene.id, 2.40, 4.20, 85, 20)

    # Lotes com validade (inclui um próximo do vencimento p/ gerar alerta)
    db.add(Lot(produto_id=arroz.id, numero="L-2026-01",
               validade=date.today() + timedelta(days=180), quantidade=50))
    db.add(Lot(produto_id=cafe.id, numero="L-2026-07",
               validade=date.today() + timedelta(days=20), quantidade=4))

    db.add(StockMovement(produto_id=arroz.id, tipo="ENTRADA", quantidade=50,
                         motivo="Compra", usuario_id=admin.id))
    db.add(StockMovement(produto_id=arroz.id, tipo="SAIDA", quantidade=2,
                         motivo="Venda inicial", usuario_id=caixa.id))

    db.commit()
    db.close()
    print("Banco populado com sucesso.")
    print("Acessos demo (senha: %s):" % DEMO_PASSWORD)
    print("  super@nexoerp.com  (superadmin)")
    print("  admin@nexoerp.com  (admin)")
    print("  caixa@nexoerp.com  (funcionario)")
    print("  cliente@nexoerp.com (cliente)")


if __name__ == "__main__":
    seed()
