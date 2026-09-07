# Notas da Nuvem

Aplicação de exemplo para o desafio da **Aula 06 — Segurança de Rede em Nuvem I** (Segurança para Computação em Nuvem, CESAR School).

Uma aplicação Flask bem simples: guarda pequenas notas de texto em um banco PostgreSQL. **A aplicação em si não é o ponto da atividade** — o que importa é a infraestrutura AWS que vai hospedá-la. Trate este código como o "que roda dentro do container"; o desafio de verdade está descrito na apostila da Aula 06.

## O que você recebe aqui

- `app.py` — a aplicação Flask (rotas `/` e `/health`).
- `templates/index.html` — a única página HTML.
- `requirements.txt` — dependências Python.
- `.env.example` — quais variáveis de ambiente a aplicação espera.

**Não há Dockerfile neste repositório.** Escrever o Dockerfile é parte do seu desafio — a apostila da Aula 06 te guia passo a passo em como fazer isso.

## Variáveis de ambiente

A aplicação lê a configuração do banco inteiramente de variáveis de ambiente — nunca edite `app.py` para colocar credenciais fixas (lembra a Aula 05?).

| Variável       | Para quê serve                                  | Exemplo (RDS)                                      |
|----------------|--------------------------------------------------|-----------------------------------------------------|
| `DB_HOST`      | Endpoint do banco                                | `seu-rds.xxxxxxxxxx.us-east-1.rds.amazonaws.com`     |
| `DB_PORT`      | Porta do PostgreSQL                              | `5432`                                               |
| `DB_NAME`      | Nome do banco de dados                           | `notasdb`                                            |
| `DB_USER`      | Usuário do banco                                 | `notas_app`                                          |
| `DB_PASSWORD`  | Senha do usuário do banco                        | *(defina a sua ao criar o RDS)*                      |
| `APP_PORT`     | Porta em que a aplicação escuta (opcional)       | `8080` (padrão)                                      |

Copie `.env.example` para `.env` e preencha com os valores do seu próprio RDS quando chegar nessa etapa do desafio.

## Testando localmente, sem Docker (opcional, mas recomendado)

Se você já tem um PostgreSQL rodando na sua máquina (ou quiser usar um container avulso do Postgres — veja a apostila), pode rodar a aplicação direto com Python antes mesmo de pensar em containerizar:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=notasdb
export DB_USER=notas_app
export DB_PASSWORD=uma_senha_de_teste

python3 app.py
# acesse http://localhost:8080
```

## Próximos passos

A apostila da Aula 06 tem o passo a passo completo a partir daqui: como escrever o Dockerfile, como buildar e testar a imagem localmente, e como enviar a imagem para o Amazon ECR. A configuração da AWS a partir daí (VPC, subnets, bastion, EC2, RDS, VPC Endpoints) é o desafio — está descrita na apostila, mas resolvê-la é com você.
