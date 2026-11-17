# Gramática do subconjunto de Python

Este documento detalha a gramática apresentada no README (seção **Gramática do subconjunto**). Ela
define **exatamente** o que o parser (`backend/parser.py`) reconhece: cada regra vira uma função com
o mesmo nome no parser, e o mesmo texto aparece na tela, no campo **regra** de cada nó da árvore e de
cada erro sintático.

## 1. Gramática formal (EBNF)

Notação: `{ x }` repete `x` zero ou mais vezes, `[ x ]` torna `x` opcional, `|` separa alternativas
e `"x"` é um terminal escrito literalmente. Nomes em MAIÚSCULAS são categorias de token da Etapa 3.

```ebnf
programa     = { comando } ;
comando      = ( atribuicao | expressao ) NOVA_LINHA ;
atribuicao   = IDENTIFICADOR "=" expressao ;
expressao    = exp_ou ;
exp_ou       = exp_e { "or" exp_e } ;
exp_e        = exp_nao { "and" exp_nao } ;
exp_nao      = "not" exp_nao | comparacao ;
comparacao   = soma { ( "==" | "!=" | "<" | ">" | "<=" | ">=" ) soma } ;
soma         = termo { ( "+" | "-" ) termo } ;
termo        = unario { ( "*" | "/" | "//" | "%" ) unario } ;
unario       = ( "+" | "-" ) unario | potencia ;
potencia     = primario [ "**" unario ] ;
primario     = atomo { "(" [ argumentos ] ")" } ;
argumentos   = expressao { "," expressao } ;
atomo        = IDENTIFICADOR | LITERAL_INTEIRO | LITERAL_REAL
             | LITERAL_STRING | LITERAL_BOOLEANO | "None" | "(" expressao ")" ;
```

- **Símbolo inicial:** `programa`.
- **Não terminais (15):** `programa`, `comando`, `atribuicao`, `expressao`, `exp_ou`, `exp_e`,
  `exp_nao`, `comparacao`, `soma`, `termo`, `unario`, `potencia`, `primario`, `argumentos`, `atomo`.
- **Terminais:** os tokens produzidos pelo scanner da Etapa 3 (tabela abaixo).

## 2. Terminais e categorias de token

O scanner da Etapa 3 **não precisou de nenhuma mudança**: todos os terminais da gramática já eram
produzidos por ele.

| Terminal na gramática | Categoria do token (Etapa 3) | Lexemas |
| --- | --- | --- |
| `IDENTIFICADOR` | `IDENTIFICADOR` | `idade`, `print`, `média` |
| `LITERAL_INTEIRO` | `LITERAL_INTEIRO` | `17` |
| `LITERAL_REAL` | `LITERAL_REAL` | `1.75` |
| `LITERAL_STRING` | `LITERAL_STRING` | `"Ana"` |
| `LITERAL_BOOLEANO` | `LITERAL_BOOLEANO` | `True`, `False` |
| `"None"`, `"and"`, `"or"`, `"not"` | `PALAVRA_RESERVADA` | os próprios |
| `"="`, `"+"`, `"-"`, `"*"`, `"/"`, `"//"`, `"%"`, `"**"`, `"=="`, `"!="`, `"<"`, `">"`, `"<="`, `">="` | `OPERADOR` | os próprios |
| `"("`, `")"`, `","` | `DELIMITADOR` | os próprios |
| `NOVA_LINHA` | `NOVA_LINHA` | quebra de linha que encerra um comando, ou fim do código |

As outras palavras reservadas do Python (`if`, `while`, `def`...) são reconhecidas pelo scanner, mas
**não aparecem na gramática**. Se uma delas surgir, o parser explica que ela está fora do subconjunto
ou que não pode ser usada como nome de variável.

## 3. Precedência e associatividade

Cada nível de precedência é um não terminal. Quanto **mais embaixo** na gramática, **mais forte** o
operador, ou seja, ele fica mais embaixo na árvore e é calculado primeiro. A ordem é a mesma do
Python, e um teste automático confere isso contra o módulo `ast` do próprio Python.

| Nível (do mais fraco ao mais forte) | Operadores | Associatividade | Regra |
| --- | --- | --- | --- |
| 1 | `or` | esquerda | `exp_ou` |
| 2 | `and` | esquerda | `exp_e` |
| 3 | `not` (unário) | direita (`not not a`) | `exp_nao` |
| 4 | `==` `!=` `<` `>` `<=` `>=` | **encadeada**, como no Python: `a < b < c` vale `a < b and b < c` e vira **um único nó** `COMPARACAO` com os operadores `["<", "<"]` e três operandos | `comparacao` |
| 5 | `+` `-` | esquerda | `soma` |
| 6 | `*` `/` `//` `%` | esquerda | `termo` |
| 7 | `+` `-` (unários) | direita (`- - x`) | `unario` |
| 8 | `**` | **direita** | `potencia` |
| 9 | chamada `f(...)` | esquerda (`f(1)(2)` chama o resultado de `f(1)`) | `primario` |
| 10 | valores, nomes, `( ... )` | | `atomo` |

Exemplos (todos conferidos nos testes):

| Código | Como o parser agrupa | Por quê |
| --- | --- | --- |
| `10 + 5 * 2` | `10 + (5 * 2)` | `*` (nível 6) é mais forte que `+` (nível 5) |
| `20 - 5 - 3` | `(20 - 5) - 3` | `-` é associativo à esquerda: a repetição `{ }` vai juntando pela esquerda |
| `(10 + 5) * 2` | `(10 + 5) * 2` | os parênteses voltam ao topo (`expressao`) dentro de `atomo` |
| `2 ** 3 ** 2` | `2 ** (3 ** 2)` | o expoente chama `unario` de novo, e por isso a potência associa à direita |
| `-2 ** 2` | `-(2 ** 2)` | `**` (nível 8) é mais forte que o menos unário (nível 7), como no Python |
| `a or b and c` | `a or (b and c)` | `and` é mais forte que `or` |
| `not a == b` | `not (a == b)` | `not` é mais fraco que a comparação |
| `0 <= nota < 10` | uma comparação com dois operadores | comparação encadeada, igual ao Python |

### Por que essa gramática serve para um parser descendente recursivo

- **Sem recursão à esquerda.** Uma regra como `soma = soma "+" termo` faria a função `soma` chamar a
  si mesma sem consumir nenhum token, num laço infinito. Por isso a gramática usa repetição:
  `soma = termo { "+" termo }`. O parser lê o primeiro `termo` e, enquanto vier `+` ou `-`, lê outro
  e junta o resultado à esquerda. É isso que dá a associatividade à esquerda.
- **Escolha olhando à frente.** Em quase todas as regras, o token atual basta para decidir qual
  alternativa seguir (LL(1)). A única exceção é `comando`: um `IDENTIFICADOR` pode começar tanto uma
  atribuição (`x = 1`) quanto uma expressão (`x + 1`). O parser olha **dois** tokens: se o segundo for
  `=`, é atribuição. Por isso a gramática é LL(1) em todas as regras menos essa, que é LL(2).

| Não terminal | Pode começar com (conjunto FIRST) |
| --- | --- |
| `atomo`, `primario`, `potencia` | `IDENTIFICADOR`, os literais, `None`, `(` |
| `unario`, `termo`, `soma`, `comparacao` | `+`, `-` e os de `atomo` |
| `exp_nao`, `exp_e`, `exp_ou`, `expressao` | `not` e os de `unario` |
| `argumentos` | os de `expressao` |
| `comando` | os de `expressao` (atribuição: `IDENTIFICADOR` seguido de `=`) |

## 4. O que está e o que não está no subconjunto

**Suportado:**
- atribuição de um valor a um nome (`idade = 17`);
- expressões aritméticas, relacionais (inclusive encadeadas) e lógicas, com a precedência do Python;
- parênteses;
- menos e mais unários;
- chamadas de função com zero ou mais argumentos (`print()`, `print("a", x)`, `max(a, min(b, c))`) e
  chamadas encadeadas (`f(1)(2)`);
- uma expressão sozinha como comando (`print(x)`, `x + 1`);
- comandos separados por quebra de linha;
- uma expressão quebrada em várias linhas dentro de parênteses;
- linhas em branco e comentários.

**Fora do escopo.** O parser mostra um erro explicando por quê:

| Construção | Exemplo | Mensagem do parser |
| --- | --- | --- |
| Blocos e indentação | `if x:`, `while`, `for`, `def` | a palavra reservada não faz parte do subconjunto |
| Palavra reservada como nome | `if = 2`, `None = 1` | não pode ser usada como nome de variável |
| Operadores compostos | `x += 1` | sugere `x = x + 1` |
| Atribuição múltipla | `a = b = 1` | uma atribuição por linha |
| Tuplas, listas, dicionários | `x = 1, 2`, `[1]`, `{}` | `,` fora de chamada; `[`, `]`, `{`, `}` já são erro léxico |
| Atribuir a algo que não é nome | `17 = x`, `f() = 1` | só um nome pode receber valor |
| Vírgula sobrando nos argumentos | `f(1,)` | depois de `,` deve vir mais um argumento (o Python aceitaria) |
| Strings coladas | `print("a" "b")` | era esperado `,` ou `)` (no Python seria concatenação implícita) |
| Vários comandos por linha | `x = 1; y = 2` | `;` já é erro léxico |

## 5. Exemplos

### Válidos

```python
resultado = 10 + 5 * 2
subtracao = 20 - 5 - 3
com_parenteses = (10 + 5) * 2
```

```python
idade = 17
pode_votar = idade >= 16 and not (idade > 70)
print("Vota?", pode_votar)
```

AST de `resultado = 10 + 5 * 2`, como aparece na tela:

```
■ Programa
└── ■ Atribuição: resultado = …
    ├── ● Identificador: resultado
    └── ◆ Adição (+)
        ├── ● Inteiro: 10
        └── ◆ Multiplicação (*)
            ├── ● Inteiro: 5
            └── ● Inteiro: 2
```

### Inválidos (com erros intencionais)

Exemplo 10 da interface. O parser encontra os 4 erros, um por linha:

```python
x = 5 +
y = * 2
z = (1 + 2))
17 = idade
```

| Linha | Mensagem | Regra violada |
| --- | --- | --- |
| 1 | `Erro sintático na linha 1, coluna 8: expressão incompleta: depois de '+' era esperado um valor, mas o fim da linha chegou antes.` | `atomo = ...` |
| 2 | `Erro sintático na linha 2, coluna 5: depois de '=' era esperado um valor (número, texto, nome ou '('), mas foi encontrado o operador '*'. Há dois operadores seguidos: entre eles precisa haver um valor.` | `atomo = ...` |
| 3 | `Erro sintático na linha 3, coluna 12: este ')' está sobrando: não há nenhum '(' aberto para ele fechar.` | `atomo = ...` |
| 4 | `Erro sintático na linha 4, coluna 4: só um nome (identificador) pode receber um valor com '='. O lado esquerdo da atribuição deve ser um nome, como em idade = 17.` | `atribuicao = IDENTIFICADOR "=" expressao` |

Outros exemplos:

| Código | Erro |
| --- | --- |
| `y = (3 + ` | o código terminou antes de fechar o parêntese aberto na linha 1, coluna 5 |
| `print(` | o código terminou antes de fechar o parêntese aberto na linha 1, coluna 6 |
| `print("a" "b")` | era esperado `,` entre os argumentos ou `)` para fechar a chamada de `print` |
| `= = 17` | um comando não pode começar com `=` |
| `x = 1 2` | era esperado o fim do comando depois de `1`; talvez falte um operador |
| `if x` | a palavra reservada `if` não faz parte do subconjunto |

## 6. Recuperação de erros

O parser usa o **modo pânico, sincronizado em `NOVA_LINHA`**. Quando encontra um erro, ele:
1. registra o erro;
2. descarta os tokens até a próxima `NOVA_LINHA`, ou seja, até o fim do comando;
3. continua analisando o comando seguinte.

Por isso o aluno vê **um erro por comando**, de todos os comandos com problema, sem os "erros em
cascata" que um mesmo engano geraria. Há uma exceção, igual ao Python: um parêntese aberto e não
fechado faz o comando continuar nas linhas seguintes, então todas elas viram um único erro.

## 7. Código com erro léxico

Como registrado em [fluxograma.md](fluxograma.md), **o parser roda mesmo quando a análise léxica
encontrou erro**. Assim o aluno vê os erros léxicos e os sintáticos de uma vez.

O parser **pula os comandos que contêm um erro léxico**. Num comando como `x = 1 @ 2`, o scanner
descarta o `@`, e o parser receberia `x = 1 2`: ele apontaria "falta um operador", um erro que o aluno
não cometeu. Para evitar isso, um comando (da primeira linha até a sua `NOVA_LINHA`) que cobre alguma
linha com erro léxico não é analisado. As linhas puladas voltam na resposta, em `linhas_ignoradas`, e
a tela avisa o aluno. Todos os outros comandos são analisados normalmente.

## 8. Limite de tamanho da árvore

Para que entradas como `((((((((...` ou `1 + 1 + 1 + ...` (milhares de vezes) não travem o servidor
nem a tela, o parser recusa, com um erro sintático explicado, expressões aninhadas ou longas demais:
- mais de 100 chamadas recursivas abertas ao mesmo tempo;
- uma AST com altura acima de 250 níveis;
- uma árvore de derivação com altura acima de 400 níveis.

Na prática, cabem até 35 níveis de parênteses e até 248 operações seguidas na mesma expressão, o
que é muito mais do que um exercício precisa.
