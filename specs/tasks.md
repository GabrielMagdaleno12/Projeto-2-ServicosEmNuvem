# Tarefas — Sistema de Gestão de Academia

Projeto 2 · Serviços em Nuvem · 2026.02. Complementa `specs/spec.md` e `specs/design.md`.

Legenda: [x] feito · [ ] pendente

## Aula 3 — Infraestrutura e CRUD (entrega 23/10)

### Rede (VPC)
- [x] Criar a VPC `academia-vpc` na região us-east-1
- [x] Criar a subnet pública `academia-publica`
- [x] Criar as subnets privadas `academia-privada-1` e `academia-privada-2`, em zonas de disponibilidade distintas
- [x] Criar a route table pública `academia-rt-publica` com rota 0.0.0.0/0 para o Internet Gateway
- [x] Criar a route table privada `academia-rt-privada`, sem rota para a internet, com o Gateway Endpoint do S3
- [x] Não usar NAT Gateway (custo)

### Segurança
- [x] Criar os Security Groups `academia-sg-lambda` e `academia-sg-rds`
- [x] Liberar a porta 3306 do RDS apenas para os outros Security Groups (sem 0.0.0.0/0)
- [x] Documentar os Security Groups em `docs/seguranca.md`

### Banco de dados (RDS)
- [x] Criar o RDS `academia-db` nas subnets privadas, com Publicly accessible = Não
- [x] Aplicar o schema e os dados de exemplo (`sql/01_schema.sql` e `sql/02_seed.sql`) por meio da Lambda `academia-dbinit`

### CRUD do RF-01 (HU-01 a HU-05)
- [x] Publicar a API (API Gateway + Lambda) com as rotas de planos, alunos, aulas e inscrições
- [x] Publicar o front-end estático no S3
- [x] Testar o CRUD pela API ao vivo, contra o RDS privado:
  - criar e editar plano
  - criar e editar aluno
  - CPF duplicado bloqueado (409 "CPF já cadastrado")
  - excluir plano em uso bloqueado (409)
  - criar aula e inscrever aluno
  - aula lotada bloqueada (409 "Aula lotada")
  - excluir inscrição, aula, aluno e plano (204)
- [ ] Testar o CRUD clicando no site do S3 (criar, editar, excluir e provocar erros)

### Documentação e evidências
- [x] Criar este `specs/tasks.md`
- [x] Criar `docs/seguranca.md`
- [ ] Preencher os IDs reais de VPC, subnets e Security Groups em `docs/seguranca.md`
- [ ] Subir os scripts SQL para `sql/` (`01_schema.sql` e `02_seed.sql`)
- [ ] Subir o código das Lambdas para `backend/` e o front-end para `frontend/`
- [ ] Anexar os prints em `docs/evidencias/`

## Aula 4 — Upload, processamento e relatórios (entrega 30/10)

- [ ] RF-02 / HU-06: upload de foto e atestado por URL pré-assinada (Lambda `presign`, CORS no bucket de uploads)
- [ ] RF-03 / HU-07: Lambda de miniatura disparada por ObjectCreated em `uploads/`, gravando os metadados no RDS
- [ ] RF-04 / HU-08: `GET /relatorios/ocupacao-aulas`
- [ ] RF-04 / HU-09: `GET /relatorios/alunos-por-plano`
- [ ] Atualizar `specs/design.md` para refletir o que realmente está rodando (engine e versão do RDS, rotas)
- [ ] Escrever no README o passo a passo para recriar tudo em uma nova sessão do Learner Lab (RNF-03)

## Observações

- O Learner Lab encerrado mantém os recursos, mas o RDS fica parado. Ao reiniciar o lab, aguardar o RDS voltar a ficar Available antes da demonstração ao vivo.
- Não usar Reset no lab: ele apaga tudo o que foi criado.
- Os IDs dos recursos mudam se algo for recriado. Os scripts e o front leem o endereço da API de `config.js`.
