# Registro de testes

Cada execução relevante fica registrada aqui, da mais recente para a mais antiga.

---

## 2026-11-17: Etapa 4A revisada, parser alinhado ao fluxograma e à gramática do README

**O que mudou e por quê.** A primeira versão do parser (registro abaixo) seguia duas decisões que
divergiam dos documentos do artigo (`docs/fluxograma.md`, `docs/casos-de-teste.md` e a seção de
gramática do README):
- o parser não rodava com erro léxico;
- a resposta guardava a análise sintática num objeto `sintatico`.

O autor decidiu seguir os documentos do artigo. Ficou assim:
- **O parser roda mesmo com erro léxico.** Os comandos que contêm um erro léxico são pulados e
  informados em `linhas_ignoradas`, para não gerar erros sintáticos inventados.
- **A resposta passou a ter `ast`, `derivacao`, `erros_sintaticos` e `linhas_ignoradas` no topo.**
  `sucesso` passou a valer para léxico **e** sintático (CT-17). `tokens` e `erros` não mudaram.
- **A gramática é a do README:**
  - comparação encadeada (`a < b < c` vira um nó `COMPARACAO` com a lista de operadores);
  - chamadas encadeadas (`f(1)(2)`);
  - sem vírgula final nos argumentos;
  - regras renomeadas para `exp_ou`, `exp_e`, `exp_nao` e `atomo`.

**Comando** (montando o código atual no container; veja a falha 3):

```bash
docker compose run --rm --no-deps -v "<pasta>/backend:/app" backend pytest -q -p no:cacheprovider
```

**Resultado:** 415 aprovados, 0 reprovados.

Testes acrescentados ou reescritos:
- **Casos de `docs/casos-de-teste.md`:** CT-01 a CT-06, CT-14 a CT-20, CT-23 a CT-25 e CT-27,
  marcados nos testes com o número do caso.
- **Comparação encadeada e chamadas encadeadas:** unitários e diferencial contra o `ast` do Python.
- **Comandos com erro léxico:**
  - o comando é pulado e o resto é analisado;
  - um erro sintático em outra linha continua sendo apontado;
  - um comando de várias linhas com erro léxico no meio é pulado inteiro;
  - um erro numa linha sem tokens não atrapalha;
  - uma string não fechada pula só a sua linha.
- **API:** formato novo, CT-17 (`sucesso` agora considera o sintático) e CT-27.

**Falhas encontradas e correções:**
1. **`None = 1`:** o teste esperava "só um nome pode receber valor", mas a mensagem passou a ser "a
   palavra reservada 'None' não pode ser usada como nome de variável". A mensagem nova é a correta,
   porque `None` é palavra reservada (CT-18). O caso foi movido para o teste de palavra reservada.
   Não é um afrouxamento: a expectativa ficou mais específica.
2. **Limite de aninhamento:** o teste do maior aninhamento aceito usava 38 níveis, medido na gramática
   antiga. A gramática nova tem um nível a mais (`atomo`), e o limite real passou a ser 35. O valor
   foi medido de novo antes de ajustar o teste, e o `docs/gramatica.md` foi atualizado.
3. **Resultado falso por imagem desatualizada:** sem acesso ao Docker Hub, o `docker compose build`
   falhou ao consultar a imagem base, e o `pytest` rodou na imagem **antiga**, mostrando "391 passed"
   com o código velho. Percebi porque a contagem não mudou e conferi o arquivo dentro do container. A
   partir daí, os testes rodaram com a pasta `backend/` montada no container, ou seja, com o código atual.
4. **Script de edição corrompeu strings:** um script que editava `test_api.py` transformou sequências
   `\n` em quebras de linha reais, e o arquivo deixou de compilar. As strings foram corrigidas à mão.

**Mutação:**

| Defeito injetado | Detectado? |
| --- | --- |
| O parser deixa de pular os comandos com erro léxico | Sim (5 testes) |
| A comparação aceita só um operador (`while` virou `if`) | Sim (5 testes) |

**Pendências:**
- reconstruir a imagem do backend quando a conexão voltar;
- tela, testes de navegador e documentação (Etapa 4B).

---

## 2026-11-17: Etapa 4A, parser (análise sintática) no backend

**Tipos:** unitário (`tests/test_parser.py`), diferencial contra o Python real
(`tests/test_parser_vs_python.py`), endpoints (`tests/test_api.py`) e regressão (scanner e validação,
sem alteração).

**Comando:**

```bash
docker compose run --rm backend pytest -v
```

**Resultado:** 391 aprovados, 0 reprovados (eram 232 na Etapa 3).

| Arquivo | O que cobre |
| --- | --- |
| `test_parser.py` | Cada construção (atribuição, cada valor, cada operador aritmético, relacional, lógico e unário, chamadas com 0 a N argumentos, chamadas aninhadas, vários comandos, expressão solta, expressão em várias linhas dentro de parênteses, combinação de construções); 20 casos de precedência e associatividade (`10 + 5 * 2`, `20 - 5 - 3`, `(10 + 5) * 2`, `2 ** 3 ** 2`, `-2 ** 2`, `a or b and c`, `not a == b`...); parênteses que não viram nó; formato e consistência dos nós; posições de início e fim (inclusive em várias linhas); ordem de construção (filho antes do pai); programa vazio e só com comentários; árvore de derivação (as folhas são exatamente os tokens; ela tem os não terminais e os parênteses e é maior que a AST); cada tipo de erro com `encontrado`, `esperado`, `regra`, linha e coluna; recuperação (um erro por comando, sem cascata); 6 entradas patológicas que viram erro em vez de travar; integração com os exemplos da Etapa 3 |
| `test_parser_vs_python.py` | Para 27 programas válidos, a AST tem a **mesma estrutura** da gerada pelo módulo `ast` do Python. Para 9 programas inválidos, o Python também os rejeita, ou seja, não há falso erro |
| `test_api.py` | Novo objeto `sintatico` (AST, derivação, erros, decisão sobre erro léxico, programa vazio, aninhamento extremo sem erro 500, aninhamento máximo aceito serializa sem erro, mensagens sem detalhes internos); os campos da Etapa 3 continuam idênticos |

**Falhas encontradas e correções:**
1. **Expectativas erradas nos testes novos, corrigidas antes da primeira execução:**
   - `x = ()` estava na lista "o Python também rejeita", mas é uma tupla vazia válida. Foi retirado
     dessa lista; o nosso parser recusa porque tuplas estão fora do subconjunto, e isso está
     documentado.
   - `a + b >= c * d != e` estava na lista de programas válidos, mas é uma comparação encadeada,
     fora do subconjunto. Foi trocado por `a + b >= c * d`.
   - O teste da ordem de construção esperava 7 nós, mas `r = 10 + 5 * 2` gera 8, contando o
     identificador `r`.
2. **Regressão detectada:** `test_analisar_codigo_valido_retorna_tokens` e
   `test_analisar_so_comentario_tem_sucesso_sem_tokens` (Etapa 3) falharam porque comparavam a
   resposta **inteira** com `==`, e a resposta ganhou o campo `sintatico`. A mudança é intencional:
   o contrato da Etapa 4 acrescenta um campo e mantém os outros. Os testes passaram a comparar os
   campos da Etapa 3, que precisam continuar idênticos, e a exigir que o único campo a mais seja
   `sintatico`. Os valores esperados não mudaram.

**Verificação dos próprios testes (mutação),** em container descartável:

| Defeito injetado no parser | Detectado? |
| --- | --- |
| Precedência de `and` e `or` trocada | Sim (diferencial) |
| Potência associativa à esquerda | Sim (diferencial) |
| `*` acrescentado ao nível do `+` | Não teve efeito: o `*` continua sendo consumido antes, no `termo`. É uma mutação equivalente, não uma falha dos testes |
| `*` **movido** do `termo` para o nível do `+` | Sim (6 testes) |

**Pendências:** a tela ainda não mostra a árvore nem os erros sintáticos (Etapa 4B).

---

## 2026-10-29: Etapa 3B, tela didática da análise léxica

**Tipos:** interface, integração e ponta a ponta (Playwright/Chromium), implantação e regressão
(backend inteiro e testes de navegador da Etapa 2).

**Comandos:**

```bash
docker compose up --build -d
docker compose --profile testes run --rm testes   # navegador
docker compose run --rm backend pytest -v         # backend (regressão da Etapa 3A)
```

**Resultado:**

| Conjunto | Aprovados | Reprovados |
| --- | --- | --- |
| Navegador (`testes/`) | 74 | 0 |
| Backend (`backend/tests/`) | 232 | 0 |
| **Total** | **306** | **0** |

Testes novos em `testes/test_analise_lexica.py` (33):
- **Tabela:** tipo, lexema, linha, coluna, descrição e cabeçalho.
- **Código colorido:** um elemento por token, com a classe da categoria. Sem as marcas ↵, o texto é
  idêntico ao código digitado, e o alinhamento continua certo com acentos e emoji.
- **Contagem por categoria.**
- **Erros:** os 3 erros do exemplo 7 com linha e coluna, o erro sublinhado no código, a string não
  fechada e a seção de erros que some quando não há erro.
- **Entradas inválidas:** 7 entradas "lixo" não geram erro de JavaScript e a tela continua
  funcionando depois.
- **HTML no código:** aparece como texto e não vira HTML.
- **Só comentário:** zero tokens.
- **Passo a passo:** avança, volta, destaca o token no código e na tabela, para no último token;
  Reproduzir percorre tudo, Pausar interrompe e uma nova análise reinicia.
- **Explicação:** a seção "O que é token e lexema?".
- **Celular:** sem rolagem horizontal em 375 px.
- **Prints:** `interface.png`, `erros-lexicos.png` e `celular.png`.

Testes da Etapa 2 atualizados por **mudança intencional de contrato** (a resposta agora é a análise
léxica):
- `test_digitar_e_analisar` e `test_editar_exemplo_e_analisar`: a mensagem passou a contar tokens.
- `test_cada_exemplo_e_aceito_pelo_backend` virou dois testes: os 5 exemplos sem erro dão sucesso e
  os 2 com erro intencional mostram os erros.
- Novo teste `test_falha_de_comunicacao_esconde_analise_anterior`: uma falha não pode deixar a
  tabela da análise anterior na tela.

**Falhas encontradas e correções:**
1. **Regressão detectada:** `test_implantacao.py::test_endpoint_de_analise_responde_atraves_do_nginx`
   falhou com `KeyError: 'recebido'`. O teste da Etapa 2 ainda conferia o contrato antigo. O código
   estava certo (a mudança de contrato era intencional), então o teste foi atualizado para o contrato
   novo, que confere `sucesso` e os lexemas.
2. **Layout no celular:** o print `celular.png` mostrou a tabela espremida, com linhas muito altas, e
   os botões do passo a passo quebrando em duas linhas. O teste automático passava, porque não havia
   rolagem horizontal na página. **Correção:** a tabela ganhou largura mínima e rola dentro do próprio
   quadro, e os botões ficaram menores e sem quebra. Rodei de novo os testes de celular: 2 aprovados.

**Validação de instalação limpa:**
1. Apaguei as imagens do projeto (`docker compose --profile testes down --rmi local`).
2. Clonei a branch `etapa-3` numa pasta nova.
3. Rodei `docker compose up --build -d`: o backend ficou `healthy`.
4. Os dois comandos de teste passaram: 232 e 74 aprovados, 0 reprovados.

O print `interface.png` gerado no clone saiu com alguns pixels diferentes do versionado, porque o
destaque do passo a passo tem uma transição de 0,2 s. É uma diferença visual só, sem impacto nos testes.

**Limitações / pendências:**
- os testes de navegador usam só o Chromium;
- não há testes automáticos de acessibilidade (contraste, leitor de tela);
- a lista de exemplos aparece em dois lugares (`frontend/site/exemplos.js` e `testes/test_interface.py`).
  Se um exemplo mudar, o teste falha e avisa.

---

## 2026-10-29: Etapa 3A, scanner (análise léxica) no backend

**Tipos:** unitário (`tests/test_scanner.py`), diferencial contra o Python real
(`tests/test_scanner_vs_python.py`), endpoints (`tests/test_api.py`) e regressão (`tests/test_validacao.py`).

**Comando:**

```bash
docker compose run --rm backend pytest -v
```

**Resultado:** 232 aprovados, 0 reprovados.

| Arquivo | O que cobre |
| --- | --- |
| `test_scanner.py` | Formato do token; cada palavra reservada do Python; nomes parecidos com reservadas; identificadores (com `_` e acentos); inteiros, reais (`.5`, `3.`), strings (aspas simples e duplas, escapes, emoji), booleanos; `17` × `"17"`; descrição cita o tipo Python; cada operador e delimitador; maior casamento (`a===b`, `2***3`); comentários e espaços ignorados; posição (várias linhas, acentos, emoji, tab); regras da `NOVA_LINHA` (fim sem `\n`, linhas em branco, comentário, dentro de parênteses, `\r\n`); cada erro léxico com localização (caractere inválido, string não fechada, número malformado, três aspas); acúmulo de erros e continuação; casos de borda (vazio, só espaços, só comentários, token no fim, 1.000 linhas) |
| `test_scanner_vs_python.py` | Para 16 programas válidos, os lexemas, linhas e colunas do nosso scanner são **idênticos** aos do `tokenize` da biblioteca padrão do Python |
| `test_api.py` | 200 com tokens e `sucesso: true` (formato exato); 200 com `sucesso: false` e erros com localização; vários erros acumulados; só comentário; os 400 da Etapa 2 (regressão); 500 genérico |
| `test_validacao.py` | Regressão da Etapa 2, sem alteração |

**Verificação dos próprios testes (mutação):** injetei dois defeitos no scanner, dentro de um container
descartável, para conferir se o teste diferencial os detecta:
- **Removi o operador `<=`:** o teste diferencial falhou, como esperado.
- **Tab passou a contar como 2 colunas:** o teste diferencial **não** falhou, porque nenhum programa
  dele tinha tab. Só o teste unitário pegava o defeito. **Correção:** acrescentei o programa
  `x\t=\t1\ty = x` ao diferencial. Com a mesma mutação, ele agora falha.

**Mudança intencional:** a resposta 200 da Etapa 2 (`recebido`, `mensagem`, `linhas`, `caracteres`)
foi substituída por `sucesso`, `tokens` e `erros`. Os testes dessa resposta foram reescritos para o
novo contrato. As respostas 400 e 500 não mudaram.

**Pendências:** a tela ainda espera o formato antigo e mostra "erro inesperado" depois de analisar.
Isso será corrigido na Etapa 3B, junto com a exibição didática dos tokens e os testes de navegador.

---

## 2026-10-21: Etapa 2B, tela principal, exemplos e testes de navegador

**Tipos:** implantação, interface, integração e ponta a ponta (Playwright/Chromium), além da
regressão do backend.

**Comandos:**

```bash
docker compose up --build -d
docker compose --profile testes run --rm testes   # navegador
docker compose run --rm backend pytest -v         # regressão do backend (Etapa 2A)
```

**Resultado:**

| Conjunto | Aprovados | Reprovados |
| --- | --- | --- |
| Navegador (`testes/`) | 38 | 0 |
| Backend (`backend/tests/`), regressão | 48 | 0 |
| **Total** | **86** | **0** |

| Arquivo | O que cobre | Testes |
| --- | --- | --- |
| `test_implantacao.py` | Página e arquivos estáticos servidos; `/api/saude` e `/api/analisar` acessíveis *pelo Nginx* (comunicação entre containers) | 4 |
| `test_interface.py` | Título e linguagem; campo, botão, resultado e seletor; fonte monoespaçada; ≥3 exemplos; digitar, editar, substituir; caracteres especiais; código preservado após analisar; cada exemplo carrega seu código; novo exemplo substitui o anterior e o código digitado; exemplo editável; opção vazia não apaga; selecionar exemplo não envia requisição | 17 |
| `test_ponta_a_ponta.py` | Digitar → analisar → mensagem com contagem; corpo enviado igual ao campo (acentos, emoji, tab); cada exemplo aceito pelo backend; editar exemplo e analisar; vazio/espaços orientam e **não** enviam requisição; validação não bloqueia entrada válida depois; erro 400 do backend exibido (limite de tamanho); falha de rede (mensagem, botão reabilitado, código preservado) e recuperação; erro 500 sem expor detalhes; botão desabilitado durante o envio; geração do print | 17 |

**Validação de instalação limpa:**
1. Apaguei as imagens do projeto (`docker compose --profile testes down --rmi local`).
2. Clonei a branch `etapa-2` numa pasta nova.
3. Rodei `docker compose up --build -d`: o backend ficou `healthy` e o frontend subiu `Up`.
4. Os dois comandos de teste passaram: 48 e 38 aprovados, 0 reprovados.

**Evidência:** `docs/evidencias/interface.png`, gerado pelo teste `test_gera_print_da_interface`.

**Falhas encontradas:** nenhuma nos testes. Um problema de ambiente: o download da imagem do Playwright
(921 MB comprimidos) foi interrompido uma vez e retomado, sem impacto no código.

**Mudança intencional:** a tela "Hello, World!" da Etapa 1 foi substituída pela tela principal. A
pendência registrada na Etapa 2A (a tela antiga chamando `/api/hello`) foi resolvida.

**Limitações / pendências:**
- os testes de navegador usam só o Chromium (Firefox e WebKit não foram testados);
- não há testes de acessibilidade nem de layout em telas pequenas;
- a lista de exemplos aparece em dois lugares (`frontend/site/exemplos.js` e `testes/test_interface.py`). Se um exemplo mudar, o teste falha e avisa.

---

## 2026-10-21: Etapa 2A, backend (`/api/analisar`, `/api/saude`, validações)

**Tipos:** unitário (`tests/test_validacao.py`) e endpoints (`tests/test_api.py`).

**Comando:**

```bash
docker compose run --rm backend pytest -v
```

**Resultado:** 48 aprovados, 0 reprovados.

| Arquivo | O que cobre | Testes |
| --- | --- | --- |
| `test_validacao.py` | Código aceito (válido, com erro intencional, caracteres especiais, limite exato), código preservado sem alteração, vazio/espaços, tipos errados, campo ausente, corpo que não é objeto, acima do limite | 26 |
| `test_api.py` | `/api/saude`; 200 com formato e contagem; caracteres especiais; 400 para sem corpo, JSON malformado, Content-Type errado, JSON que não é objeto, campo ausente, tipo errado, vazio, espaços e acima do limite; 405 no GET; 404; remoção de `/api/hello`; 500 genérico sem vazar detalhes | 22 |

**Verificação de implantação (manual, via `curl` pelo Nginx em `localhost:8080`):**
- `docker compose up --build -d`: o backend fica `healthy` e o frontend sobe depois dele;
- `GET /api/saude` → 200;
- `POST /api/analisar` com `idade = 17` → 200;
- `POST /api/analisar` com espaços → 400.

**Falhas encontradas:** nenhuma.

**Mudança intencional:** `/api/hello` (Etapa 1) foi removido. O teste `test_hello_da_etapa_1_foi_removido`
documenta essa decisão.

**Pendências:** a tela da Etapa 1 ainda chama `/api/hello`, que não existe mais. Ela será substituída
na Etapa 2B, junto com os testes de interface e ponta a ponta.
