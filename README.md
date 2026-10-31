# Sistema de Gestão de Academia
Projeto 2 · Serviços em Nuvem · 2026.02

Integrantes: André Drumond, Eduardo Barbizan, Gabriel Henrique, Gustavo Frainer.

Landing page: http://academia-landing-147963671881.s3-website-us-east-1.amazonaws.com

Sistema (front-end com CRUD, upload e relatórios): http://academia-frontend-147963671881.s3-website-us-east-1.amazonaws.com

API (HTTP API, 19 rotas): `https://fy5la5bb48.execute-api.us-east-1.amazonaws.com`

> **Ambiente atual:** em 31/10/2026 o ambiente inteiro foi recriado, igual ao original, em um novo Learner Lab (conta 147963671881), porque o lab anterior estava no limite de crédito. Os prints marcados como do lab original em `docs/evidencias/` continuam válidos porque a arquitetura é a mesma; só os IDs mudaram. O RDS fica **parado** quando não está em uso (custo); para demonstrar, iniciar `academia-db` e esperar `Available`.

## Documentação
- Especificação: [specs/spec.md](specs/spec.md)
- Design/arquitetura/ADRs: [specs/design.md](specs/design.md)
- Log de IA: [specs/ia-log.md](specs/ia-log.md)
- Tarefas: [specs/tasks.md](specs/tasks.md)
- Segurança e Security Groups: [docs/seguranca.md](docs/seguranca.md)

## Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| `specs/spec.md` | Problema, personas, histórias com critérios de aceite, aplicação de RF-01 a RF-05 |
| `specs/design.md` | Arquitetura, modelo ER, rotas da API, Security Groups, ADRs |
| `specs/tasks.md` | Tarefas com ID, requisito, responsável e status |
| `specs/ia-log.md` | Log de uso de IA (prompt, o que gerou, o que foi aceito, rejeitado ou corrigido) |
| `docs/seguranca.md` | Rede e Security Groups explicados |
| `docs/evidencias/` | Prints do console da AWS e do sistema funcionando |
| `sql/` | `01_schema.sql` e `02_seed.sql` (aplicados pela Lambda `academia-dbinit`) |
| `backend/` | Código das Lambdas (Python 3.12): `crud`, `dbinit`, `presign`, `miniatura`, `relatorios` |
| `frontend/` | Site estático (HTML/JS) publicado no S3 |

## Como criar tudo do zero (RNF-03 e RNF-05)

Região `us-east-1`. Tudo é criado pelo console ou CloudShell, sem IaC. As Lambdas usam a `LabRole` (o Learner Lab não permite criar roles). **Não usar NAT Gateway** e não clicar em Reset no lab (apaga tudo).

**1. Rede (VPC).**
- VPC `academia-vpc`, `10.0.0.0/16`.
- Subnet pública `academia-publica` e subnets privadas `academia-privada-1` e `academia-privada-2`, as duas privadas em zonas de disponibilidade diferentes (o DB Subnet Group exige 2 AZs).
- Route table `academia-rt-publica` com `0.0.0.0/0` para o Internet Gateway, associada à subnet pública.
- Route table `academia-rt-privada` **sem** rota para a internet, associada às duas privadas.
- VPC Gateway Endpoint (gratuito) `com.amazonaws.us-east-1.s3`, associado à `academia-rt-privada`. Sem ele, as Lambdas na VPC não alcançam o S3.

**2. Security Groups** (detalhes em `docs/seguranca.md`).
- `academia-sg-lambda`: sem entrada; saída TCP 3306 para `academia-sg-rds` e HTTPS 443 para o prefix list do S3.
- `academia-sg-rds`: entrada TCP 3306 **somente** com origem `academia-sg-lambda`. Nunca `0.0.0.0/0`.

**3. Banco (RDS).** DB Subnet Group com as duas subnets privadas. RDS MySQL `db.t3.micro` chamado `academia-db`, com *Publicly accessible = No* e `academia-sg-rds`. Esperar o status `Available`.

**4. Schema e dados.** Criar a Lambda `academia-dbinit` (VPC, `academia-sg-lambda`) com as variáveis `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` e executá-la uma vez. Ela aplica `sql/01_schema.sql` e `sql/02_seed.sql`. A senha só existe nas variáveis de ambiente, nunca no repositório (RNF-02).

**5. CRUD e API.**
- Lambda de CRUD (VPC, `academia-sg-lambda`, mesmas variáveis do passo 4) com as rotas de planos, alunos, aulas e inscrições listadas em `specs/design.md`.
- API Gateway **HTTP API** com as rotas do CRUD. **Ativar o CORS da API** (origem = URL do site, métodos `GET,POST,PUT,DELETE,OPTIONS`, header `Content-Type`).
- As rotas da Aula 4 (abaixo) entram na mesma API.

**6. Front-end.** Bucket do site com *static website hosting* e leitura pública só do site (`s3:GetObject`). Criar `frontend/config.js` a partir de `config.example.js` com a URL da API (a URL muda se a API for recriada) e publicar os arquivos no bucket.

Depois siga a seção da Aula 4 abaixo (uploads, miniatura e relatórios).

## Aula 4 · Upload, evento S3 → Lambda → RDS e relatórios

**Código:** `backend/presign/`, `backend/miniatura/`, `backend/relatorios/` (Python 3.12) e `frontend/aula4.js` + `frontend/aula4-secoes.html` (trecho acrescentado ao front publicado). A tabela `arquivo` já existe no schema; não houve alteração de banco.

**Pacotes das Lambdas.** Cada pasta de `backend/` vira um ZIP com o `handler.py` na raiz mais as dependências
(`pip install --target build/<lambda> --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all: pymysql` e, só para a miniatura, também `Pillow`).

**Recursos criados (console/CloudShell, sem IaC, conforme RNF-05):**

1. Bucket de uploads `academia-uploads-<id-da-conta>`: Block Public Access ligado e CORS configurado como abaixo.
   CORS do bucket de uploads (o navegador envia `Content-Type` no PUT; sem `AllowedHeaders` o upload falha):
   ```json
   [{"AllowedHeaders": ["*"], "AllowedMethods": ["PUT", "GET", "HEAD"],
     "AllowedOrigins": ["http://<bucket-do-site>.s3-website-us-east-1.amazonaws.com"],
     "ExposeHeaders": ["ETag"], "MaxAgeSeconds": 3000}]
   ```
2. Lambda `academia-presign` (LabRole, VPC, `academia-sg-lambda`, 15 s, 256 MB). Variáveis: `UPLOAD_BUCKET`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.
3. Lambda `academia-miniatura` (mesma rede, 30 s, 512 MB). Mesmas variáveis, sem `UPLOAD_BUCKET`. Gatilho S3: `s3:ObjectCreated:*` com **prefixo `uploads/`** (miniaturas vão para `thumbs/`, o que evita loop de eventos).
4. Lambda `academia-relatorios` (mesma rede). Variáveis: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.
5. API Gateway (HTTP API): `POST /alunos/{id}/arquivos/presign` e `GET /alunos/{id}/arquivos` → presign; `GET /relatorios/ocupacao-aulas` e `GET /relatorios/alunos-por-plano` → relatorios.
6. Front: o conteúdo de `frontend/aula4.js` fica no fim do `app.js` e as seções de `frontend/aula4-secoes.html` entram no `index.html`; depois é só publicar no bucket do site.

**Teste executado (28/10/2026):** upload de um PNG 400x300 → miniatura 150x150 em `thumbs/` → `tamanho_bytes`, `largura`, `altura` e `chave_thumb` gravados no RDS em cerca de 1 s → log "Miniatura criada ... linhas atualizadas no RDS: 1" no CloudWatch. Os dois relatórios respondem HTTP 200 e aparecem na aba Relatórios do site.

**Teste executado (31/10/2026, ambiente recriado):** criação de aluno (201), exclusão de plano em uso (409), CPF inválido (400), upload de um PNG 800x600 → miniatura → `tamanho_bytes`, largura e altura gravados no RDS (status PROCESSADO), e os dois relatórios com HTTP 200.

**Recriar em uma nova sessão do Learner Lab (RNF-03):**
1. Iniciar o lab e esperar o RDS ficar `Available` (o endpoint não muda ao parar e iniciar).
2. Conferir se a URL da API é a mesma do `config.js`; se algo foi recriado, atualizar `DB_HOST` nas Lambdas e o `config.js` do front.
3. Se o bucket de uploads precisar ser recriado: Block Public Access, CORS (com `AllowedHeaders` e a origem do site), gatilho no prefixo `uploads/` e a permissão da Lambda `academia-miniatura`.
4. Ao terminar, clicar em **End Lab** (o RDS e as instâncias ficam parados; custos de NAT/EIP/armazenamento não existem neste projeto).
