# Visualizador Léxico de Python

Software educacional da disciplina de Compiladores. É uma página web que vai mostrar a alunos do
ensino médio como o Python lê um programa: o analisador léxico classifica cada valor pela forma
como ele foi escrito (`17` é inteiro, `"17"` é string), antes de o programa ser executado.

> **Etapa 1:** só a fundação do projeto (frontend + backend no Docker exibindo "Hello, World!").
> A análise léxica vem nas próximas etapas.

## Linguagem analisada: Python

Escolhemos Python porque os literais são fáceis de distinguir pela forma escrita, porque é a
linguagem usada em cursos técnicos e porque a biblioteca padrão (`tokenize`) permite conferir o
resultado contra o interpretador real.

**Subconjunto tratado:** literais (inteiro, float, string, booleano), nomes de variáveis e
atribuição simples, por exemplo `idade = 17`.

**Fica de fora por enquanto:** condicionais, laços, funções e classes.

## Arquitetura

```
navegador → localhost:8080 (Nginx) ─┬→ index.html
                                    └→ /api/* → backend:5000 (Flask)
```

O Nginx serve a página e repassa as chamadas `/api/` para o Flask. Assim o navegador conversa
com um único endereço.

```
.
├── docker-compose.yml   # sobe os dois containers
├── backend/             # API em Flask
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/            # página estática servida pelo Nginx
    ├── index.html
    ├── nginx.conf
    └── Dockerfile
```

## Pré-requisitos

- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e **aberto**
  (já inclui o Docker Compose)
  - Docker **24 ou superior** (testado com 29.6)
  - Docker Compose **v2 ou superior** (testado com v5.3), usado como `docker compose`, com espaço

Para conferir:

```bash
docker --version
docker compose version
```

## Como executar

```bash
git clone https://github.com/MarcoTulioSilv/analisador_lexico_python visualizador-lexico-python
cd visualizador-lexico-python
docker compose up --build -d
```

Depois, abra **http://localhost:8080** no navegador. Deve aparecer **Hello, World!**.

Se aparecer **"Erro: o backend não respondeu."**, o frontend subiu, mas o backend não. Veja o
motivo com `docker compose logs backend`.

## Como encerrar

```bash
docker compose down
```

Para remover também as imagens criadas pelo projeto:

```bash
docker compose down --rmi local
```

## Próximas etapas

1. Analisador léxico do subconjunto
2. Tela de visualização dos tokens
3. Análise sintática

## Autor

Marco Túlio Silva Oliveira — Disciplina de Compiladores
