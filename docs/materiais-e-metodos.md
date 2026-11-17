# Materiais e Métodos: registros da Etapa 4 (análise sintática)

Registros técnicos para a seção de Materiais e Métodos do artigo. O fluxo do sistema está em
[fluxograma.md](fluxograma.md), os casos de teste e critérios definidos antes da implementação em
[casos-de-teste.md](casos-de-teste.md), a gramática em [gramatica.md](gramatica.md) e o histórico de
execuções em [testes.md](testes.md).

## 1. Materiais (tecnologias)

| Componente | Tecnologia | Observação |
| --- | --- | --- |
| Interface | HTML, CSS e JavaScript sem framework, servidos por Nginx 1.27 | As árvores são listas aninhadas: não há biblioteca gráfica |
| Backend | Python 3.12 + Flask 3.1 | Um endpoint, `POST /api/analisar` |
| Analisador léxico | Python, escrito à mão (`backend/scanner.py`) | Etapa 3, sem alteração na Etapa 4 |
| Analisador sintático | Python, descendente recursivo escrito à mão (`backend/parser.py`) | Sem gerador de parser |
| Testes | pytest 8.3 (backend) e Playwright 1.49 com Chromium (navegador) | Tudo roda em containers |
| Ambiente | Docker e Docker Compose | Um comando sobe o sistema; outro roda os testes |

## 2. Método: decisões técnicas da análise sintática

### 2.1 Estratégia de análise

O parser é **descendente recursivo, escrito à mão**: cada não terminal da gramática (EBNF, 15 regras)
vira uma função com o mesmo nome.

| Alternativa considerada | Por que não foi usada |
| --- | --- |
| Parser preditivo LL(1) com tabela | A tabela esconde do aluno a correspondência regra → código, e exigiria calcular e manter FIRST/FOLLOW à mão |
| Ascendente LR/LALR (Yacc, Bison, PLY) | É mais difícil de explicar para o público (ensino médio), e as mensagens de erro são genéricas |
| Geradores (ANTLR, Lark) | Acrescentam dependência e uma etapa de geração no build, e o aluno não vê o reconhecimento acontecendo |
| Parser do próprio Python (módulo `ast`) | Não permite mensagens didáticas nem mostrar as regras. É usado **só nos testes**, como oráculo |

Escolhas da gramática:
- **Sem recursão à esquerda:** repetição `{ }` no lugar dela, o que dá associatividade à esquerda.
- **Potência à direita:** recursão à direita em `potencia → unario`.
- **Uma regra por nível de precedência,** na mesma ordem do Python.
- **LL(1) em todas as regras, exceto `comando`:** ele olha dois tokens (`x =` contra `x +`), ou seja, LL(2).

### 2.2 Representação

O parser produz **duas árvores** na mesma passada:
- **AST:** 22 tipos de nó com atributos padronizados. Cada nó tem:
  - a posição de início e fim (linha e coluna);
  - a **regra da gramática** que o reconheceu;
  - um **número de ordem de construção**, em que os filhos nascem antes do pai.
- **Árvore de derivação:** um nó por não terminal, com a sua regra, e um nó por terminal (token). As
  folhas são exatamente a sequência de tokens.

Os parênteses aparecem só na derivação. Na AST, a forma da árvore já expressa o agrupamento. Exemplo:
para `resultado = 10 + 5 * 2`, a AST tem 8 nós e a derivação, 31.

### 2.3 Tratamento de erros

- **Mensagens:** cada erro traz o que foi encontrado, o que era esperado, a regra da gramática e a
  posição. A mensagem é escrita para o contexto, por exemplo: "depois de '+' era esperado um valor";
  "o parêntese aberto na linha 1, coluna 5 não foi fechado"; "operadores compostos como '+=' não
  fazem parte do subconjunto. Em vez de x += 1, escreva x = x + 1".
- **Recuperação:** modo pânico, sincronizado em `NOVA_LINHA`. Gera um erro por comando, sem cascata.
- **Erro léxico:** o parser roda mesmo assim, mas pula os comandos que contêm erro léxico. Eles são
  informados em `linhas_ignoradas`, para não gerar diagnósticos sobre tokens que faltam. A decisão e
  a justificativa estão em [fluxograma.md](fluxograma.md).
- **Robustez:** há limites de aninhamento (100 chamadas recursivas, altura 250 na AST e 400 na
  derivação). Entradas como `((((...` viram erro sintático explicado, e não falha do servidor.

### 2.4 Apresentação ao estudante

Recursos implementados na interface. Esta tabela serve para comparar com as ferramentas descritas nos
artigos pesquisados, e a coluna de comparação deve ser preenchida a partir deles:

| Recurso | Implementado | Onde | Presente nas ferramentas dos artigos? |
| --- | --- | --- | --- |
| Tabela de tokens com tipo, lexema, linha e coluna | Sim | Etapa 3 | |
| Código colorido por categoria de token | Sim | Etapa 3 | |
| Passo a passo do scanner (animado) | Sim | Etapa 3 | |
| AST navegável (expandir/recolher) | Sim | Etapa 4 | |
| Clicar num nó destaca o trecho do código | Sim | Etapa 4 | |
| Regra gramatical exibida em cada nó | Sim | Etapa 4 | |
| Árvore de derivação ao lado da AST, com contagem comparativa | Sim | Etapa 4 | |
| Construção da AST passo a passo (animada) | Sim | Etapa 4 | |
| Erros sintáticos com encontrado, esperado e regra violada | Sim | Etapa 4 | |
| Recuperação de erros (vários erros por análise) | Sim | Etapa 4 | |
| Erros léxicos e sintáticos exibidos juntos e diferenciados | Sim | Etapa 4 | |
| Forma do nó por categoria (■ ◆ ●), além da cor | Sim | Etapa 4 | |
| Uso no celular | Sim | Etapas 3 e 4 | |
| Gramática formal documentada (EBNF, FIRST, precedência) | Sim | `docs/gramatica.md` | |
| Tutorial para estudantes | Sim | `docs/tutorial.md` | |
| Explicações com IA | Não | Diferencial opcional, não implementado | |
| Exportação da AST em JSON | Não | Ela está disponível na resposta da API, mas não há botão de exportação | |
| Filtro por tipo de nó | Não | | |

## 3. Critérios de avaliação

Definidos antes da implementação, em [casos-de-teste.md](casos-de-teste.md):

1. **Corretude contra um oráculo:**
   - para os programas válidos, a sequência de tokens tem que ser igual à do `tokenize` do Python, e
     a estrutura da AST, igual à do `ast` do Python;
   - tudo o que o parser recusa, o Python também tem que recusar.
2. **Cobertura dos 28 casos planejados:** válidos, com erro léxico, com erro sintático e de borda.
   Nenhum fica só em teste manual.
3. **Regressão:** nenhum teste das etapas anteriores pode passar a falhar sem uma justificativa
   documentada.
4. **Robustez:** entradas inválidas, aninhadas ou grandes não podem derrubar o servidor nem a interface.
5. **Qualidade dos próprios testes (mutação):** defeitos injetados de propósito (precedência trocada,
   associatividade invertida, recuperação desligada) precisam ser detectados.

**Resultado na Etapa 4:** todos os critérios atendidos. Os números estão em [testes.md](testes.md).
