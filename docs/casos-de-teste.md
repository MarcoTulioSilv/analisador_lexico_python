# Casos de teste documentados

Os 28 casos abaixo foram definidos antes da implementação do parser, junto com os
critérios de avaliação da Etapa 4, para que o resultado não seja julgado por
critérios escolhidos depois de conhecê-lo. Cada caso indica o arquivo de teste
que o cobre.

Quando estes casos foram definidos, os arquivos de teste do parser ainda não
existiam. Eles foram criados na Etapa 4, e a coluna "Arquivo de teste" foi
atualizada para onde cada caso ficou de fato. Nos testes, cada caso aparece
marcado com o seu número (por exemplo, `# CT-27`). Nos casos em que o
comportamento esperado muda nesta etapa, a linha diz o que muda.

Nenhum caso fica apenas em teste manual.

## Categoria: código válido

| ID | Entrada | Resultado esperado | Análise | Arquivo de teste |
| --- | --- | --- | --- | --- |
| CT-01 | `idade = 17` | Quatro tokens, AST de atribuição com literal inteiro, sem erros | Léxica e sintática | `backend/tests/test_scanner.py`, `backend/tests/test_parser.py` |
| CT-02 | `idade = 17` e `idade_texto = "17"` | `17` como `LITERAL_INTEIRO` e `"17"` como `LITERAL_STRING`; duas atribuições na AST | Léxica e sintática | `backend/tests/test_scanner.py`, `backend/tests/test_parser.py` |
| CT-03 | `altura = 1.75` e `aprovado = True` | `LITERAL_REAL` e `LITERAL_BOOLEANO` reconhecidos | Léxica e sintática | `backend/tests/test_scanner.py`, `backend/tests/test_parser.py` |
| CT-04 | `r = (2 + 3) * 4 ** 2` | AST com precedência correta e potência associativa à direita | Sintática | `backend/tests/test_parser.py` |
| CT-05 | `maior = idade >= 18 and not False` | `>=` como um token; AST com `and` acima da comparação | Léxica e sintática | `backend/tests/test_scanner.py`, `backend/tests/test_parser.py` |
| CT-06 | `print("Idade:", idade + 1)` | Chamada com dois argumentos na AST | Sintática | `backend/tests/test_parser.py` |
| CT-07 | Linha de comentário, linha em branco e um comando | Comentário e linha em branco não geram token nem `NOVA_LINHA` | Léxica | `backend/tests/test_scanner.py` |
| CT-08 | Programa com literais, expressões, comentário e chamada | Tokens corretos, AST válida, nenhum erro | Léxica e sintática | `backend/tests/test_api.py`, `testes/test_ponta_a_ponta.py` |

## Categoria: erro léxico

| ID | Entrada | Resultado esperado | Análise | Arquivo de teste |
| --- | --- | --- | --- | --- |
| CT-09 | `email = ana@escola` | Erro de caractere não reconhecido na coluna do `@` | Léxica | `backend/tests/test_scanner.py`, `testes/test_analise_lexica.py` |
| CT-10 | `nome = "Ana` | Erro de string não fechada com linha e coluna | Léxica | `backend/tests/test_scanner.py` |
| CT-11 | `preco = 10.5.2` | Um único erro de número malformado, não vários | Léxica | `backend/tests/test_scanner.py` |
| CT-12 | `t = """texto"""` | Erro de string de três aspas fora do subconjunto | Léxica | `backend/tests/test_scanner.py` |
| CT-13 | Três linhas, cada uma com um erro diferente | Três erros acumulados, análise não interrompida no primeiro | Léxica | `backend/tests/test_scanner.py` |

## Categoria: erro sintático

Todos os casos desta categoria são novos: hoje o backend não detecta erro
sintático, e o único efeito de um programa malformado é o que o scanner relata.

| ID | Entrada | Resultado esperado | Análise | Arquivo de teste |
| --- | --- | --- | --- | --- |
| CT-14 | `x =` | Erro indicando operando esperado após `=` | Sintática | `backend/tests/test_parser.py` |
| CT-15 | `x = 1 + * 2` | Erro de operador onde se esperava operando | Sintática | `backend/tests/test_parser.py` |
| CT-16 | `print(` | Erro de parêntese não fechado, com fim inesperado | Sintática | `backend/tests/test_parser.py` |
| CT-17 | `= = 17` | Erro sintático; hoje este código é aceito, e passará a não ser | Sintática | `backend/tests/test_parser.py`, `backend/tests/test_api.py` (`sucesso` passou de `true` a `false`) |
| CT-18 | `if = 2` | Erro de palavra reservada onde se esperava identificador | Sintática | `backend/tests/test_parser.py` |
| CT-19 | `y = (3 + ` | Erro de fim inesperado no meio da expressão | Sintática | `backend/tests/test_parser.py` |
| CT-20 | `x += 1` | Erro sintático: divergência conhecida do escopo léxico, agora detectada | Léxica e sintática | `backend/tests/test_scanner.py`, `backend/tests/test_parser.py` |

## Categoria: borda

| ID | Entrada | Resultado esperado | Análise | Arquivo de teste |
| --- | --- | --- | --- | --- |
| CT-21 | Campo vazio | HTTP 400 com mensagem pedindo código | Validação | `backend/tests/test_validacao.py`, `backend/tests/test_api.py` |
| CT-22 | Apenas espaços e quebras de linha | HTTP 400 com a mesma mensagem | Validação | `backend/tests/test_validacao.py` |
| CT-23 | Apenas uma linha de comentário | Nenhum token, nenhum erro, AST vazia; mensagem adequada na interface | Léxica e sintática | `backend/tests/test_scanner.py`, `backend/tests/test_parser.py`, `backend/tests/test_api.py`, `testes/test_arvore.py` |
| CT-24 | Um único comando sem quebra de linha final | `NOVA_LINHA` emitido no fim do arquivo | Léxica | `backend/tests/test_scanner.py` |
| CT-25 | Expressão com dez níveis de parênteses aninhados | AST correta; árvore ainda navegável na interface | Sintática | `backend/tests/test_parser.py`, `testes/test_arvore.py` |
| CT-26 | Mais de 10.000 caracteres | HTTP 400 com mensagem de limite excedido | Validação | `backend/tests/test_validacao.py` |
| CT-27 | `x = 1 @ 2` seguido de `y = 2 + 3` | Erro léxico na primeira linha, segunda linha analisada normalmente; verifica a decisão de projeto do fluxograma | Léxica e sintática | `backend/tests/test_parser.py`, `backend/tests/test_api.py`, `testes/test_arvore.py` |
| CT-28 | Identificadores com acento e string com emoji | Linha e coluna corretas, contadas em caracteres | Léxica | `backend/tests/test_scanner.py` |

## Testes diferenciais

Além dos casos acima, dois testes comparam a ferramenta com o próprio Python,
usado como oráculo:

| Arquivo | O que compara |
| --- | --- |
| `backend/tests/test_scanner_vs_python.py` | A sequência de tokens do scanner contra o módulo `tokenize`, nos casos CT-01 a CT-08 |
| `backend/tests/test_parser_vs_python.py` | A forma da AST contra o módulo `ast`, nos casos CT-01 a CT-08 |

As divergências esperadas e justificadas (o subconjunto não cobre tudo que o
Python cobre) estão listadas como exceções explícitas dentro de cada arquivo,
nunca silenciadas.

## Linha de base

Ao fim da Etapa 3 o repositório tinha **306 testes aprovados**: 232 de backend
(pytest) e 74 de navegador (Playwright). Esse é o número contra o qual a Etapa 4
deve ser comparada: nenhum teste existente deve passar a falhar, com a única
exceção documentada do CT-17, cuja expectativa muda junto com o significado do
campo `sucesso`.

## Resultado na Etapa 4

Todos os 28 casos passam: **533 testes aprovados**, sendo 416 de backend e 117
de navegador. O detalhe de cada execução está em [testes.md](testes.md).

Além do CT-17, dois testes da Etapa 3 precisaram de ajuste:
`test_analisar_codigo_valido_retorna_tokens` e
`test_analisar_so_comentario_tem_sucesso_sem_tokens`. Eles comparavam a
resposta **inteira** com `==`, e a resposta ganhou campos novos (`ast`,
`derivacao`, `erros_sintaticos`, `linhas_ignoradas`). Os valores esperados de
`tokens` e `erros` **não mudaram**; os testes passaram a comparar só esses
campos e a exigir exatamente o conjunto novo de campos.

## Como executar

```bash
# backend
docker compose run --rm backend python -m pytest

# navegador
docker compose --profile testes run --rm testes
```
