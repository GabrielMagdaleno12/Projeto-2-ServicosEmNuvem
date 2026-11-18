# Segurança e Security Groups

Região: us-east-1 (Learner Lab, conta 727687112230 — ambiente recriado em 17/11/2026 a partir deste repositório; os IDs abaixo são os do lab atual). Complementa a seção 4 de `specs/design.md`.

## Princípios

- O banco de dados não é acessível pela internet. Ele fica em subnets privadas, com Publicly accessible = Não.
- A única porta aberta para o banco é a 3306 (MySQL), e somente a partir do Security Group `academia-sg-lambda`, nunca para 0.0.0.0/0.
- As subnets privadas não têm rota para a internet e não há NAT Gateway (custo). As Lambdas acessam o S3 pelo Gateway Endpoint.
- Não há bastion nem EC2 de administração: os scripts SQL rodam pela Lambda `academia-dbinit`, que usa o `academia-sg-lambda`.
- Credenciais do banco ficam em variáveis de ambiente das Lambdas e não são versionadas no Git.

## Recursos de rede

| Recurso | Nome | ID real | Observação |
|---|---|---|---|
| VPC | `academia-vpc` | `vpc-0b524a398aba541ab` | 10.0.0.0/16 (conforme design.md) |
| Subnet pública | `academia-publica` | `subnet-0c428c5aa8feed6b8` | Rota 0.0.0.0/0 para o Internet Gateway |
| Subnet privada 1 | `academia-privada-1` | `subnet-090a10367497eab81` | AZ diferente da privada 2 |
| Subnet privada 2 | `academia-privada-2` | `subnet-01a412ad0cf47d66c` | Exigência do DB Subnet Group (2 AZs) |
| Route table pública | `academia-rt-publica` | `rtb-0fdbc14e8ddcd05ec` | 0.0.0.0/0 para o Internet Gateway |
| Route table privada | `academia-rt-privada` | `rtb-0bb665728c1792eab` | Sem rota para a internet; só o Gateway Endpoint do S3 |
| Gateway Endpoint do S3 | `com.amazonaws.us-east-1.s3` | `vpce-0d28f370744a50889` | Tipo Gateway, associado à `academia-rt-privada` |
| RDS | `academia-db` | `academia-db.ct2ihogecbfl.us-east-1.rds.amazonaws.com` | MySQL 8.0.46, db.t3.micro; Acessível publicamente: Não |

## Security Groups

| Security Group | ID real | Entrada (inbound) | Saída (outbound) | Uso |
|---|---|---|---|---|
| `academia-sg-lambda` | `sg-0633cdea25bd2505a` | Nenhuma | Restrita ao RDS (TCP 3306 para o `academia-sg-rds`) e ao S3 (HTTPS 443) | Lambdas dentro da VPC (CRUD e `academia-dbinit`) |
| `academia-sg-rds` | `sg-0c881fa68207de160` | TCP 3306 somente do `academia-sg-lambda` (origem = Security Group, não IP nem CIDR) | Nenhuma necessária | Banco de dados RDS |

### Por que cada regra existe

- **`academia-sg-lambda` sem entrada:** as Lambdas só iniciam conexões (para o banco e para o S3). Ninguém precisa abrir conexão com elas, então não há regra de entrada.
- **`academia-sg-lambda` com saída restrita:** a Lambda só precisa falar com o RDS na porta 3306 e com o S3 por HTTPS. Limitar a saída reduz o estrago se a função for comprometida.
- **`academia-sg-rds` aceitando 3306 só do `academia-sg-lambda`:** a origem é esse Security Group, e não um IP ou um CIDR. Assim, só os recursos que usam o `academia-sg-lambda` (as Lambdas) alcançam o banco, mesmo que os IPs mudem. Nenhum outro SG tem acesso ao banco.
- **`academia-sg-rds` sem saída:** o banco não inicia conexões para fora.
- **Sem 0.0.0.0/0 no banco:** nenhuma regra expõe o banco à internet.

## Como conferir no console

1. VPC > Security Groups > `academia-sg-rds` > aba "Inbound rules": porta 3306 com origem `academia-sg-lambda` (única regra).
2. VPC > Security Groups > `academia-sg-lambda` > aba "Outbound rules".
3. RDS > Databases > `academia-db`: "Publicly accessible: No".
4. VPC > Route tables > `academia-rt-privada` > aba "Routes": sem rota 0.0.0.0/0.
