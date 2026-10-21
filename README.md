# Visualizador Léxico de Python

Software educacional da disciplina de Compiladores. É uma página web que vai mostrar a alunos do
ensino médio como o Python lê um programa: o analisador léxico classifica cada valor pela forma
como ele foi escrito (`17` é inteiro, `"17"` é string), antes de o programa ser executado.

> **Situação atual (Etapa 2):** a interface já recebe o código-fonte, oferece exemplos, valida a
> entrada e envia o código ao backend, que confirma o recebimento. **A análise léxica, sintática e
> semântica ainda não está implementada**; ela vem nas próximas etapas.

## Linguagem analisada: Python

Escolhemos Python porque os literais são fáceis de distinguir pela forma escrita, porque é a
linguagem usada em cursos técnicos e porque a biblioteca padrão (`tokenize`) permite conferir o
resultado contra o interpretador real.

**Subconjunto tratado:** literais (inteiro, float, string, booleano), nomes de variáveis e
atribuição simples, por exemplo `idade = 17`.

**Fica de fora por enquanto:** condicionais, laços, funções e classes.

## Tecnologias

| Parte | Tecnologia |
| --- | --- |
| Frontend | HTML, CSS e JavaScript puro, servidos pelo Nginx |
| Backend | Python 3.12 + Flask |
| Testes do backend | pytest (test client do Flask) |
| Testes de interface e ponta a ponta | Playwright (Python), rodando num container |
| Ambiente | Docker + Docker Compose |

## Arquitetura

```
navegador → localhost:8080 (Nginx) ─┬→ página (index.html, estilo.css, exemplos.js, app.js)
                                    └→ /api/* → backend:5000 (Flask)
```

O Nginx serve a página e repassa as chamadas `/api/` para o Flask. O navegador conversa com um único
endereço (`localhost:8080`). O nome `backend` só existe dentro da rede do Docker, e quem o usa é o
Nginx, não o navegador.

```
.
├── docker-compose.yml        # backend, frontend e (perfil "testes") os testes de navegador
├── backend/                  # API em Flask
│   ├── app.py                # rotas: /api/analisar, /api/saude, erro 500 genérico
│   ├── validacao.py          # regras de validação da entrada
│   ├── tests/                # testes unitários e de endpoints (pytest)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # página estática servida pelo Nginx
│   ├── site/
│   │   ├── index.html        # estrutura da tela
│   │   ├── estilo.css
│   │   ├── exemplos.js       # programas de exemplo
│   │   └── app.js            # interação, validação no navegador e comunicação com a API
│   ├── nginx.conf
│   └── Dockerfile
├── testes/                   # testes de implantação, interface e ponta a ponta (Playwright)
└── docs/
    ├── testes.md             # registro das execuções de teste
    └── evidencias/           # print da interface gerado pelos testes
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

Não é preciso instalar Python nem Node na máquina: tudo roda dentro dos containers.

## Como executar

```bash
git clone https://github.com/MarcoTulioSilv/analisador_lexico_python visualizador-lexico-python
cd visualizador-lexico-python
docker compose up --build -d
```

Depois, abra **http://localhost:8080** no navegador.

O frontend só sobe depois que o backend responde ao `healthcheck`. Para conferir o estado dos serviços:

```bash
docker compose ps        # backend deve aparecer como "healthy"
```

Nenhuma variável de ambiente ou senha é necessária. A única porta usada na máquina é a **8080**.

## Como encerrar

```bash
docker compose down
```

Para remover também as imagens criadas pelo projeto:

```bash
docker compose down --rmi local
```

## Como usar a interface

![Interface da Etapa 2](docs/evidencias/interface.png)

1. **Escolha um exemplo** no seletor (opcional). O código do exemplo **substitui** o conteúdo do campo.
2. **Escreva, cole ou edite** o código no campo de texto, que usa fonte monoespaçada.
3. Clique em **Analisar**. Durante o envio, o botão fica desabilitado e mostra "Enviando...".
4. Veja a resposta na área **Resultado**:

| Cor | Situação | Exemplo de mensagem |
| --- | --- | --- |
| Verde | Código recebido pelo backend | `Código recebido com sucesso. (3 linha(s), 42 caractere(s))` |
| Amarelo | Problema na entrada | `Informe um código-fonte antes de solicitar a análise.` |
| Vermelho | Falha de comunicação | `Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente.` |
| Vermelho | Erro inesperado no servidor | `Ocorreu um erro inesperado. Tente novamente mais tarde.` |

O código digitado nunca é apagado pelo envio nem pelas mensagens de erro.

### Exemplos disponíveis

| Exemplo | Código | O que demonstra |
| --- | --- | --- |
| 1. Números: inteiro e float | `idade = 17`<br>`altura = 1.75` | Literais numéricos inteiro e float, atribuição |
| 2. Strings: 17 é diferente de "17" | `idade = 17`<br>`idade_texto = "17"`<br>`nome = "Ana"` | Literal string e a diferença entre `17` e `"17"`, o ponto central do projeto |
| 3. Booleanos e nomes | `aprovado = True`<br>`pendente = False`<br>`situacao = aprovado` | Literais booleanos e um nome usado como valor |
| 4. Erro intencional | `nome = "Ana` | String não fechada. Hoje o código é aceito (ainda não há análise), mas o exemplo já fica pronto para mostrar o erro léxico na próxima etapa |

## Comunicação entre frontend e backend

### `POST /api/analisar`

Requisição (JSON):

```json
{ "codigo": "idade = 17" }
```

| Situação | HTTP | Resposta |
| --- | --- | --- |
| Código aceito | 200 | `{"recebido": true, "mensagem": "Código recebido com sucesso.", "linhas": 1, "caracteres": 10}` |
| Corpo ausente, que não é JSON ou JSON malformado | 400 | `{"recebido": false, "erro": "Requisição inválida: envie um JSON no formato {\"codigo\": \"...\"}."}` |
| Campo `codigo` ausente ou que não é texto | 400 | `{"recebido": false, "erro": "O campo \"codigo\" é obrigatório e deve ser um texto."}` |
| Código vazio ou só com espaços, tabs ou quebras de linha | 400 | `{"recebido": false, "erro": "Informe um código-fonte antes de solicitar a análise."}` |
| Mais de 10.000 caracteres | 400 | `{"recebido": false, "erro": "O código excede o limite de 10.000 caracteres."}` |
| Erro inesperado no servidor | 500 | `{"recebido": false, "erro": "Erro interno no servidor. Tente novamente mais tarde."}` |

`linhas` e `caracteres` são calculados pelo backend, o que prova que o código chegou de fato.
O código **não precisa ser Python válido**: erros intencionais são aceitos, porque serão usados
nas próximas etapas para mostrar como o compilador encontra problemas.

As validações acontecem nos dois lados: o navegador barra o campo vazio antes de enviar, e o
backend repete a validação, porque não se deve confiar só na interface.

### `GET /api/saude`

Responde `200 {"status": "ok"}`. É usado pelo `healthcheck` do Docker Compose.

> **Mudança em relação à Etapa 1:** o endpoint `/api/hello` e a tela "Hello, World!" foram
> substituídos pela tela principal e por `/api/analisar`.

## Testes

São dois conjuntos, e os dois rodam via Docker:

```bash
# 1. Backend: testes unitários (validacao.py) e de endpoints (app.py)
docker compose run --rm backend pytest -v

# 2. Navegador: testes de implantação, interface, integração e ponta a ponta (Playwright)
#    Sobe backend e frontend automaticamente, se ainda não estiverem de pé.
#    Na primeira vez, baixa a imagem do Playwright (~1,5 GB).
docker compose --profile testes run --rm testes
```

| Arquivo | Tipo | O que verifica |
| --- | --- | --- |
| `backend/tests/test_validacao.py` | Unitário | Regras de validação: aceitos, vazios, espaços, tipos errados, limite |
| `backend/tests/test_api.py` | Endpoints | Códigos HTTP, formato das respostas, entradas inválidas, erro 500 sem detalhes internos |
| `testes/test_implantacao.py` | Implantação | Página e arquivos servidos, backend acessível *através do Nginx* |
| `testes/test_interface.py` | Interface | Elementos da tela, edição, caracteres especiais e cada exemplo |
| `testes/test_ponta_a_ponta.py` | Integração e ponta a ponta | Digitar → analisar → resposta; validação no navegador; erro do backend exibido; falha de rede; erro 500; botão durante o envio; print |

Os dois conjuntos juntos funcionam como **testes de regressão**: devem ser rodados a cada mudança.
O teste `test_gera_print_da_interface` grava o print em `docs/evidencias/interface.png`.

**Resultado mais recente:** todos os testes passaram. O histórico de execuções, com comandos,
contagens e falhas corrigidas, fica em [docs/testes.md](docs/testes.md).

## Limitações conhecidas

- **Ainda não há análise léxica, sintática nem semântica.** O backend só valida e confirma o recebimento do código.
- O campo de código é um `textarea` simples, sem realce de sintaxe nem numeração de linhas.
- O limite é de 10.000 caracteres por envio.
- Escolher um exemplo substitui o código do campo sem pedir confirmação.
- O backend usa o servidor de desenvolvimento do Flask, que é suficiente para uso em sala, mas não para produção.

## Próximas etapas

1. Analisador léxico do subconjunto
2. Tela de visualização dos tokens
3. Análise sintática

## Autor

Marco Túlio Silva Oliveira — Disciplina de Compiladores
