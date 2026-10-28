# Deploy no Render — Nexo ERP

Este projeto tem duas partes que sobem como dois serviços separados no Render:

- `backend/` → API FastAPI (Web Service)
- `index.html`, `cadastro.html`, `demo.html`, `assets/` → site estático (Static Site)

## Passo a passo

1. **Suba este projeto para um repositório no GitHub** (a pasta `mini-erp` inteira,
   já sem `.venv` e sem `__pycache__` — removidos e ignorados pelo `.gitignore`).

2. No [Render](https://dashboard.render.com), clique em **New +** →
   **Blueprint**, aponte para o repositório. O Render vai ler o arquivo
   `render.yaml` da raiz e criar os dois serviços automaticamente
   (`nexo-erp-api` e `nexo-erp-site`).

   *Alternativa manual (sem Blueprint):*
   - **New + → Web Service** → selecione o repo → *Root Directory*: `backend`
     → Build Command: `pip install -r requirements.txt` → Start Command:
     `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **New + → Static Site** → selecione o repo → *Root Directory*: (vazio/raiz)
     → Build Command: vazio → Publish directory: `.`

3. Depois que a API subir, copie a URL dela (algo como
   `https://nexo-erp-api.onrender.com`). Se quiser restringir o CORS a só
   o seu site, edite a env var `CORS_ORIGINS` no serviço da API com a URL
   do site estático (ex: `https://nexo-erp-site.onrender.com`).

4. **Login de demonstração** (senha `demo123` para todos):
   - `super@nexoerp.com` — superadmin
   - `admin@nexoerp.com` — admin
   - `caixa@nexoerp.com` — funcionário
   - `cliente@nexoerp.com` — cliente

## Importante sobre o banco de dados

O projeto usa **SQLite** (`nexo.db`) por padrão. No plano gratuito do Render,
o disco é **efêmero** — ou seja, os dados são resetados a cada novo deploy
(e o serviço "dorme" e reinicia sozinho após inatividade). Para um ambiente
que realmente precisa persistir dados:

1. Crie um banco **PostgreSQL gratuito** no Render (New + → PostgreSQL).
2. Copie a **Internal Database URL**.
3. No serviço da API, adicione a env var `DATABASE_URL` com esse valor
   (o `render.yaml` já deixa isso comentado, pronto para descomentar).
4. Rode `python -m app.seed` uma vez (via Shell do Render, aba do serviço)
   para popular o banco com os dados de demonstração.

## Variáveis de ambiente da API

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | gerada automaticamente pelo Render | chave do JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | validade do token |
| `DATABASE_URL` | `sqlite:///./nexo.db` | string de conexão |
| `CORS_ORIGINS` | `*` | origens liberadas, separadas por vírgula |
