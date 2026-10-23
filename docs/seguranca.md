# Segurança e Security Groups

Região: us-east-1 (Learner Lab). Complementa a seção 4 de `specs/design.md`.

## Princípios

- O banco de dados não é acessível pela internet. Ele fica em subnets privadas, com Publicly accessible = Não.
- A única porta aberta para o banco é a 3306 (MySQL), e apenas para outros Security Groups, nunca para 0.0.0.0/0.
- As subnets privadas não têm rota para a internet e não há NAT Gateway (custo). As Lambdas acessam o S3 pelo Gateway Endpoint.
- Credenciais do banco ficam em variáveis de ambiente das Lambdas e não são versionadas no Git.

## Recursos de rede

| Recurso | Nome | ID real | Observação |
|---|---|---|---|
| VPC | `academia-vpc` | _preencher_ | 10.0.0.0/16 (conforme design.md) |
| Subnet pública | `academia-publica` | _preencher_ | Rota 0.0.0.0/0 para o Internet Gateway |
| Subnet privada 1 | `academia-privada-1` | _preencher_ | AZ diferente da privada 2 |
| Subnet privada 2 | `academia-privada-2` | _preencher_ | Exigência do DB Subnet Group (2 AZs) |
| Route table pública | `academia-rt-publica` | _preencher_ | 0.0.0.0/0 para o Internet Gateway |
| Route table privada | `academia-rt-privada` | _preencher_ | Sem rota para a internet; só o Gateway Endpoint do S3 |
| RDS | `academia-db` | — | Acessível publicamente: Não; status Available |

## Security Groups

| Security Group | ID real | Entrada (inbound) | Saída (outbound) | Uso |
|---|---|---|---|---|
| `academia-sg-lambda` | _preencher_ | Nenhuma | Restrita ao RDS (TCP 3306 para o `academia-sg-rds`) e ao S3 (HTTPS 443) | Lambdas dentro da VPC |
| `academia-sg-rds` | _preencher_ | TCP 3306 apenas dos outros Security Groups | Nenhuma necessária | Banco de dados RDS |

### Por que cada regra existe

- **`academia-sg-lambda` sem entrada:** as Lambdas só iniciam conexões (para o banco e para o S3). Ninguém precisa abrir conexão com elas, então não há regra de entrada.
- **`academia-sg-lambda` com saída restrita:** a Lambda só precisa falar com o RDS na porta 3306 e com o S3 por HTTPS. Limitar a saída reduz o estrago se a função for comprometida.
- **`academia-sg-rds` aceitando 3306 só de outros Security Groups:** a origem é um Security Group, e não um IP ou um CIDR. Assim, só os recursos que usam esses SGs (as Lambdas) alcançam o banco, mesmo que os IPs mudem.
- **`academia-sg-rds` sem saída:** o banco não inicia conexões para fora.
- **Sem 0.0.0.0/0 no banco:** nenhuma regra expõe o banco à internet.

## Como conferir no console

1. VPC > Security Groups > `academia-sg-rds` > aba "Inbound rules": porta 3306 com origem em Security Groups.
2. VPC > Security Groups > `academia-sg-lambda` > aba "Outbound rules".
3. RDS > Databases > `academia-db`: "Publicly accessible: No".
4. VPC > Route tables > `academia-rt-privada` > aba "Routes": sem rota 0.0.0.0/0.

As evidências (prints) ficam em `docs/evidencias/`.

## Pendências

- Preencher a coluna "ID real" com os IDs do console (sem expor segredos).
- Confirmar os CIDRs das subnets e dos Security Groups reais e ajustar a tabela, se diferirem do design.
