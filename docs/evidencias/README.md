# Evidências da Aula 3

Prints do console da AWS e do sistema funcionando. Salve os arquivos nesta pasta com os nomes abaixo. Não incluir senhas, chaves de acesso nem tokens nos prints.

Legenda: [x] anexado · [ ] pendente

| Arquivo | O que mostrar | Tarefa | Status |
|---|---|---|---|
| `01-vpc.png` | VPC `academia-vpc` (10.0.0.0/16) e suas 3 subnets, com os IDs visíveis | T-01 a T-03, T-18 | [ ] |
| `02-rt-publica.png` | Route table `academia-rt-publica`, aba Routes: 0.0.0.0/0 para o Internet Gateway | T-04 | [ ] |
| `03-rt-privada.png` | Route table `academia-rt-privada`, aba Routes: sem 0.0.0.0/0 e com o Gateway Endpoint do S3 | T-05 | [ ] |
| `04-sg-rds-inbound.png` | `academia-sg-rds`, Inbound rules: só TCP 3306 com origem `academia-sg-lambda` | T-08 | [ ] |
| `05-sg-lambda-outbound.png` | `academia-sg-lambda`, Outbound rules: TCP 3306 para o `academia-sg-rds` e HTTPS 443 para o S3 | T-07 | [ ] |
| `06-rds-privado.png` | RDS `academia-db`: status Available e Publicly accessible = No | T-10 | [ ] |
| `07-dbinit.png` | Execução da Lambda `academia-dbinit` (schema e seed aplicados) | T-11 | [ ] |
| `08-api-crud.png` | Testes da API ao vivo: criação, 409 de CPF duplicado, 409 de aula lotada, 204 nas exclusões | T-14 | [ ] |
| `09-site-s3.png` | Site no S3 listando planos, alunos e aulas | T-13, T-15 | [ ] |
