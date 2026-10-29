# Tarefas — Sistema de Gestão de Academia

Projeto 2 · Serviços em Nuvem · 2026.02. Complementa `specs/spec.md` e `specs/design.md`.

Legenda de status: [x] feito · [ ] pendente. Requisitos (RF/RNF) conforme `specs/spec.md`, seções 6 e 7.

## Aula 3 — Infraestrutura e CRUD (entrega 23/10)

| ID | Requisito | Tarefa | Responsável | Status |
|---|---|---|---|---|
| T-01 | RNF-01 | Criar a VPC `academia-vpc` (10.0.0.0/16) na região us-east-1 | A definir | [x] |
| T-02 | RNF-01 | Criar a subnet pública `academia-publica` | A definir | [x] |
| T-03 | RNF-01 | Criar as subnets privadas `academia-privada-1` e `academia-privada-2`, em zonas de disponibilidade distintas | A definir | [x] |
| T-04 | RNF-01 | Criar a route table pública `academia-rt-publica` com rota 0.0.0.0/0 para o Internet Gateway | A definir | [x] |
| T-05 | RNF-01 | Criar a route table privada `academia-rt-privada`, sem rota para a internet, com o Gateway Endpoint do S3 | A definir | [x] |
| T-06 | RNF-05 | Não usar NAT Gateway (custo) | A definir | [x] |
| T-07 | RNF-01 | Criar os Security Groups `academia-sg-lambda` e `academia-sg-rds` | A definir | [x] |
| T-08 | RNF-01 | Liberar a porta 3306 do `academia-sg-rds` somente para o `academia-sg-lambda` (sem 0.0.0.0/0) | A definir | [x] |
| T-09 | RNF-01 | Documentar os Security Groups em `docs/seguranca.md` | A definir | [x] |
| T-10 | RF-01 / RNF-01 | Criar o RDS `academia-db` nas subnets privadas, com Publicly accessible = Não | A definir | [x] |
| T-11 | RF-01 | Aplicar o schema e os dados de exemplo (`sql/01_schema.sql` e `sql/02_seed.sql`) por meio da Lambda `academia-dbinit` | A definir | [x] |
| T-12 | RF-01 | Publicar a API (API Gateway + Lambda) com as rotas de planos, alunos, aulas e inscrições | A definir | [x] |
| T-13 | RF-05 | Publicar o front-end estático no S3 | A definir | [x] |
| T-14 | RF-01 (HU-01 a HU-05) | Testar o CRUD pela API ao vivo, contra o RDS privado: criar/editar plano e aluno; CPF duplicado bloqueado (409); excluir plano em uso bloqueado (409); criar aula e inscrever aluno; aula lotada bloqueada (409); excluir inscrição, aula, aluno e plano (204) | A definir | [x] |
| T-15 | RF-01 / RF-05 | Testar o CRUD clicando no site do S3 (criar, editar, excluir e provocar erros) | A definir | [ ] |
| T-16 | Entrega | Criar este `specs/tasks.md` | A definir | [x] |
| T-17 | RNF-01 | Criar `docs/seguranca.md` | A definir | [x] |
| T-18 | RNF-01 | Preencher os IDs reais de VPC, subnets, route tables e Security Groups em `docs/seguranca.md` | A definir | [ ] |
| T-19 | RF-01 | Subir os scripts SQL para `sql/` (`01_schema.sql` e `02_seed.sql`) | A definir | [ ] |
| T-20 | RF-01 / RF-05 | Subir o código para `backend/` e `frontend/`. Feito: `presign`, `miniatura`, `relatorios` e o trecho `frontend/aula4.*`. Falta: Lambdas de CRUD e `academia-dbinit`, `app.js`, `index.html` e `config.example.js` | A definir | [ ] |
| T-21 | Entrega | Anexar os prints em `docs/evidencias/` (lista em `docs/evidencias/README.md`) | A definir | [ ] |
| T-22 | Entrega | Registrar o uso de IA da Aula 3 em `specs/ia-log.md` | A definir | [x] |
| T-23 | RNF-04 | Alinhar `specs/design.md` com a rede real (sem bastion; sg-lambda e sg-rds) | A definir | [x] |

## Aula 4 — Upload, processamento e relatórios (entrega 30/10)

| ID | Requisito | Tarefa | Responsável | Status |
|---|---|---|---|---|
| T-24 | RF-02 / HU-06 | Upload de foto e atestado por URL pré-assinada (Lambda `presign`, CORS no bucket de uploads) | A definir | [x] |
| T-25 | RF-03 / HU-07 | Lambda de miniatura disparada por ObjectCreated em `uploads/`, gravando os metadados no RDS | A definir | [x] |
| T-26 | RF-04 / HU-08 | `GET /relatorios/ocupacao-aulas` | A definir | [x] |
| T-27 | RF-04 / HU-09 | `GET /relatorios/alunos-por-plano` | A definir | [x] |
| T-28 | RNF-04 | Atualizar `specs/design.md` para refletir o que está rodando (fluxo de upload, tabela `arquivo`, rotas, SGs) | A definir | [x] |
| T-29 | RNF-03 | Escrever no README o passo a passo para recriar tudo em uma nova sessão do Learner Lab | A definir | [x] |
| T-30 | RF-02 / RF-03 / RF-04 | Código das Lambdas da Aula 4 em `backend/` e trecho do front em `frontend/`; teste ao vivo de ponta a ponta (upload → miniatura → RDS → CloudWatch) | A definir | [x] |
| T-31 | RNF-04 | Confirmar a engine e a versão reais do RDS no console e registrá-las em `specs/design.md` (ADR-002) | A definir | [ ] |

## Observações

- O Learner Lab encerrado mantém os recursos, mas o RDS fica parado. Ao reiniciar o lab, aguardar o RDS voltar a ficar Available antes da demonstração ao vivo.
- Não usar Reset no lab: ele apaga tudo o que foi criado.
- Os IDs dos recursos mudam se algo for recriado. Os scripts e o front leem o endereço da API de `config.js`.
