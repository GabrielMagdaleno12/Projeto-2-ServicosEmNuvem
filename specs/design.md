# Design — Sistema de Gestão de Academia

> Complementa `specs/spec.md`. Região: `us-east-1` (padrão do Learner Lab).
> Status: **implementado e em execução** (Aula 4, 28/10/2026). Este documento reflete o que está rodando na conta do Learner Lab.

## 1. Diagrama de arquitetura

<img width="2102" height="847" alt="image" src="https://github.com/user-attachments/assets/465a0601-adab-437a-9378-4288280009ea" />



### Fluxo de upload (RF-02 e RF-03)
1. O front valida tipo (JPG, PNG, PDF) e tamanho (até 5 MB) e pede `POST /alunos/{id}/arquivos/presign` com nome, tipo MIME, tamanho e categoria (`foto` ou `atestado`).
2. A Lambda Presign valida de novo, **grava a linha em `arquivo`** (por isso ela fica na VPC) e devolve uma URL `PUT` pré-assinada (válida por 5 min), a chave `uploads/{aluno}/{uuid}.{ext}` e o `arquivo_id`.
3. O navegador envia o arquivo **direto ao S3** com essa URL.
4. O S3 emite `ObjectCreated` e dispara a Lambda Miniatura, que confere o tamanho real do objeto (acima de 5 MB o objeto é apagado do S3 e a linha de `arquivo` é removida), gera a miniatura 150x150 JPEG, salva em `thumbs/` e faz `UPDATE` em `arquivo` (`chave_thumb`, `tamanho_bytes`, `largura`, `altura`). O processamento fica registrado no CloudWatch Logs. Para PDF (atestado) só o tamanho é gravado.
5. O front consulta `GET /alunos/{id}/arquivos` (o bucket é privado, a resposta traz URLs `GET` pré-assinadas de 15 min) e exibe a miniatura.

> Evitar loop: o gatilho do S3 filtra pelo prefixo `uploads/`; as miniaturas ficam em `thumbs/`.

## 2. Modelo de dados (ER)

<img width="418" height="627" alt="image" src="https://github.com/user-attachments/assets/40c60a0e-74ee-4357-b5a5-0dc9b10f21c4" />


> Tabela `arquivo` como implementada: `id, aluno_id, tipo (foto|atestado), chave_s3, chave_thumb, tamanho_bytes, largura, altura, criado_em`. Não há coluna de status: um arquivo está **PENDENTE** enquanto `tamanho_bytes` é nulo e **PROCESSADO** depois que a Lambda Miniatura roda.

### Regras de integridade
- `aluno.cpf` é `UNIQUE`.
- `aluno.plano_id` usa `FOREIGN KEY ... ON DELETE RESTRICT` (não exclui plano com alunos).
- `inscricao` tem `UNIQUE (aluno_id, aula_id)` e `ON DELETE CASCADE` em `aluno_id` e `aula_id`.
- `arquivo.aluno_id` usa `ON DELETE CASCADE`.
- Vagas restantes = `aula.vagas - COUNT(inscricao)`; verificada na criação da inscrição, dentro de transação.

### Scripts SQL versionados
```
sql/
  01_schema.sql      -- CREATE TABLE
  02_seed.sql        -- dados de exemplo (planos, aulas)
```

## 3. Rotas da API

Base: `https://{api-id}.execute-api.us-east-1.amazonaws.com` (muda a cada recriação; o front lê de `config.js`).

| Método | Rota | Descrição | Lambda | História |
|---|---|---|---|---|
| GET | `/planos` | Lista planos | crud | HU-03 |
| POST | `/planos` | Cria plano | crud | HU-03 |
| PUT | `/planos/{id}` | Atualiza plano | crud | HU-03 |
| DELETE | `/planos/{id}` | Remove plano (409 se houver alunos) | crud | HU-03 |
| GET | `/alunos?busca=` | Lista/busca alunos | crud | HU-01/02 |
| GET | `/alunos/{id}` | Detalhe do aluno + arquivos | crud | HU-02/06 |
| POST | `/alunos` | Cria aluno (409 CPF duplicado) | crud | HU-01 |
| PUT | `/alunos/{id}` | Atualiza aluno | crud | HU-02 |
| DELETE | `/alunos/{id}` | Remove aluno | crud | HU-02 |
| GET | `/aulas` | Lista aulas com vagas restantes | crud | HU-04 |
| POST | `/aulas` | Cria aula | crud | HU-04 |
| PUT | `/aulas/{id}` | Atualiza aula | crud | HU-04 |
| DELETE | `/aulas/{id}` | Remove aula | crud | HU-04 |
| POST | `/aulas/{id}/inscricoes` | Inscreve aluno (409 lotada/duplicada) | crud | HU-05 |
| DELETE | `/inscricoes/{id}` | Cancela inscrição | crud | HU-05 |
| POST | `/alunos/{id}/arquivos/presign` | Valida, registra em `arquivo` e gera URL `PUT` pré-assinada | presign | HU-06 |
| GET | `/alunos/{id}/arquivos` | Lista arquivos do aluno com URLs `GET` pré-assinadas e status | presign | HU-06/07 |
| GET | `/relatorios/ocupacao-aulas` | Inscritos, vagas e % por aula | relatorios | HU-08 |
| GET | `/relatorios/alunos-por-plano` | Alunos e receita por plano | relatorios | HU-09 |

### Exemplo: relatório de ocupação
```sql
SELECT a.id, a.modalidade, a.dia_semana, a.horario, a.vagas,
       COUNT(i.id)                          AS inscritos,
       ROUND(COUNT(i.id) / a.vagas * 100, 1) AS ocupacao_pct
FROM aula a
LEFT JOIN inscricao i ON i.aula_id = a.id
GROUP BY a.id, a.modalidade, a.dia_semana, a.horario, a.vagas
ORDER BY ocupacao_pct DESC;
```

### Exemplo: alunos por plano
```sql
SELECT p.nome, COUNT(al.id) AS alunos,
       COUNT(al.id) * p.valor_mensal AS receita_estimada
FROM plano p
LEFT JOIN aluno al ON al.plano_id = p.id
GROUP BY p.id, p.nome, p.valor_mensal;
```

## 4. Rede e Security Groups

| Recurso | Detalhe |
|---|---|
| VPC | `10.0.0.0/16` |
| Subnet pública | `10.0.1.0/24`, rota `0.0.0.0/0` para Internet Gateway (sem instâncias; não há bastion) |
| Subnets privadas | `10.0.2.0/24` e `10.0.3.0/24` em AZs distintas (exigência do DB Subnet Group), **sem** rota para internet |
| NAT Gateway | **Não usar** (custo) |
| Endpoint | VPC Gateway Endpoint `com.amazonaws.us-east-1.s3` associado à route table privada |

### Security Groups

| SG | Entrada (inbound) | Saída (outbound) | Uso |
|---|---|---|---|
| `academia-sg-lambda` | nenhuma | TCP 3306 para `academia-sg-rds`; HTTPS 443 para o prefix list do S3 | Lambdas na VPC (CRUD, `academia-dbinit`, `academia-presign`, `academia-miniatura` e `academia-relatorios`) |
| `academia-sg-rds` | TCP 3306 **apenas de** `academia-sg-lambda` | nenhuma necessária | Banco de dados |

> RDS com `Publicly accessible = No`. Nenhum SG tem entrada `0.0.0.0/0` para o banco. Não há bastion nem EC2 de administração: o schema e os dados de exemplo são aplicados pela Lambda `academia-dbinit`, que usa o `academia-sg-lambda`. Detalhes em `docs/seguranca.md`.

## 5. Segurança e configuração

- Host, usuário e senha do banco ficam em **variáveis de ambiente das Lambdas**, configuradas pelo console. Nada disso vai para o Git (`.env` no `.gitignore`).
- Permissões via `LabRole` (não é possível criar roles no Learner Lab).
- Bucket de uploads **privado**; leitura via URL pré-assinada `GET`.
- O limite de 5 MB é validado em três pontos: no front, na geração da URL (tamanho declarado) e **de novo na Lambda Miniatura** (tamanho real do objeto), porque a URL pré-assinada não limita o tamanho.
- A Lambda Miniatura lê o S3 pelo VPC Gateway Endpoint (sem NAT). O Pillow vai empacotado no ZIP da função.
- Bucket do front público somente para leitura (`s3:GetObject`).
- CORS: no API Gateway (origem do site, métodos `GET,POST,PUT,DELETE,OPTIONS`) e no bucket de uploads (`PUT`, header `Content-Type`).
- Bônus possível: mover credenciais para Secrets Manager / Parameter Store.

## 6. ADRs (Architecture Decision Records)

### ADR-001 · CRUD em Lambda ou em container? (RNF-04)

- **Status:** Aceito
- **Contexto:** O CRUD (planos, alunos, aulas, inscrições) precisa de backend com acesso ao RDS. As opções são funções Lambda atrás do API Gateway ou um container (Docker) em EC2/ECS. Restrições do Learner Lab: orçamento limitado, sessão expira, IP público da EC2 muda ao reiniciar, não há criação de roles.
- **Opções consideradas:**

| Critério | Lambda + API Gateway | Container em EC2/ECS |
|---|---|---|
| Custo | Paga por invocação; ocioso ≈ 0 | Instância ligada o tempo todo consome crédito |
| IP/endereço | URL estável do API Gateway; sem IP para fixar | IP público muda ao reiniciar a sessão |
| Manutenção | Sem servidor para administrar | Patch, Docker, restart manual |
| Reaproveitamento | Já exigimos Lambda para RF-03 e RF-04; mesmo modelo de deploy | Segunda tecnologia de execução |
| Cold start | Existe (centenas de ms), aceitável para uso interno | Não existe |
| Conexão com banco | Cada invocação abre conexão; volume baixo | Pool de conexões persistente |

- **Decisão:** CRUD em **Lambda** (Python) atrás de **API Gateway HTTP API**, na mesma VPC do RDS.
- **Consequências:**
  - (+) Menor custo e nenhuma dependência de IP, o que ajuda no RNF-03 (recriar em nova sessão).
  - (+) Uma única forma de executar código para CRUD, upload e relatórios.
  - (−) Cold start no primeiro acesso.
  - (−) Lambda na VPC não tem internet; acesso ao S3 exige o VPC Gateway Endpoint.
  - (−) Reuso de conexão com o banco deve ser feito fora do handler para não esgotar conexões.

### ADR-002 · Banco relacional: MySQL no RDS
- **Contexto:** Relações 1:N e N:N, necessidade de JOIN/GROUP BY nos relatórios.
- **Decisão:** Amazon RDS **MySQL** `db.t3.micro`, subnet privada.
- **Consequências:** Modelo relacional natural para o domínio; custo baixo; precisa de DB Subnet Group com 2 AZs.

### ADR-003 · Upload por URL pré-assinada
- **Contexto:** Arquivos passando pelo API Gateway/Lambda têm limite de payload e custo maior.
- **Decisão:** O backend só **gera a URL**; o navegador envia direto ao S3.
- **Consequências:** (+) Sem limite de payload do API Gateway; (+) menos custo de Lambda; (−) exige CORS correto no bucket e validação de tipo/tamanho na geração da URL.

### ADR-004 · Front-end em S3 (site estático)
- **Contexto:** O front é HTML/JS sem renderização no servidor.
- **Decisão:** Publicar em **S3 static website hosting**.
- **Consequências:** (+) Sem servidor, sem IP; (−) apenas HTTP no endpoint do S3 (CloudFront seria bônus para HTTPS).

## 7. Estrutura sugerida do repositório

```
/
├── README.md
├── specs/            spec.md · design.md · tasks.md · ia-log.md
├── docs/             seguranca.md · evidencias/
├── sql/              01_schema.sql · 02_seed.sql
├── backend/
│   ├── crud/         handler.py
│   ├── presign/      handler.py
│   ├── relatorios/   handler.py
│   └── miniatura/    handler.py
└── frontend/         index.html · app.js · config.example.js
```

## 8. Pendências para a Aula 4 (manter o design coerente com o que roda)

- [ ] Confirmar engine/versão real do RDS.
- [ ] Anotar IDs reais de subnets e SGs (sem expor segredos).
- [x] Ajustar rotas que mudarem na implementação (acrescentada `GET /alunos/{id}/arquivos`; presign passou a gravar em `arquivo`).
- [ ] Inserir prints em `docs/evidencias/`.
