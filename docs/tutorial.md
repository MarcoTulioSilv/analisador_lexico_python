# Tutorial: como o Python lê o seu código

Este tutorial é para quem vai usar o **Visualizador Léxico de Python** pela primeira vez. Ele leva
uns 10 minutos. Abra a ferramenta em **http://localhost:8080** e vá fazendo junto.

---

## 1. Antes de executar, o Python precisa "ler"

Quando você escreve

```python
idade = 17
```

o computador não enxerga palavras: ele recebe uma fila de caracteres,
`i`, `d`, `a`, `d`, `e`, ` `, `=`, ` `, `1`, `7`. A primeira coisa que o Python faz é juntar esses
caracteres em pedaços com significado. Quem faz isso é o **analisador léxico**, também chamado de
**scanner**. É a primeira fase de um compilador ou interpretador.

É parecido com ler uma frase: antes de entender o sentido, você separa as palavras.

## 2. Três palavras para guardar

| Termo | O que é | No exemplo `idade = 17` |
| --- | --- | --- |
| **Lexema** | O pedaço de texto exato que o scanner leu | `idade`, `=`, `17` |
| **Token** | O lexema junto com a sua **categoria** e a sua **posição** | `idade` é um `IDENTIFICADOR` na linha 1, coluna 1 |
| **Erro léxico** | Um trecho que não forma nenhum token conhecido | `@` em `email = ana@escola` |

Os espaços servem só para separar os pedaços: o scanner os descarta. Os comentários (`# ...`) também
são descartados, porque são recados para quem lê o código, não para o computador.

## 3. Mão na massa: o passo a passo

1. No seletor, escolha **"2. Strings: 17 é diferente de "17""**.
2. Clique em **Analisar**.
3. No quadro **Passo a passo do scanner**, clique em **Próximo ▶** várias vezes, ou em
   **▶ Reproduzir** para ver a animação.

A cada clique, o token que o scanner acabou de ler fica **amarelo** no código e na tabela, e uma frase
explica o que aconteceu:

> Passo 3 de 12: o scanner leu 17 na linha 1, coluna 9 → LITERAL_INTEIRO (número inteiro: vira um
> objeto do tipo int).

Continue até o passo 7:

> Passo 7 de 12: o scanner leu "17" na linha 2, coluna 15 → LITERAL_STRING (texto entre aspas: vira um
> objeto do tipo str).

**Repare:** `17` e `"17"` parecem a mesma coisa, mas o scanner já os separa em categorias diferentes,
**só pela forma como foram escritos**. As aspas fazem toda a diferença. É por isso que, mais tarde,
`17 + 1` dá `18`, mas `"17" + 1` dá erro: um é número e o outro é texto.

## 4. As cores

Depois da análise, o código aparece colorido. Cada cor é uma categoria, e as etiquetas logo abaixo do
código servem de legenda e mostram quantos tokens de cada tipo foram encontrados.

| Categoria | O que é | Exemplos |
| --- | --- | --- |
| `IDENTIFICADOR` | Um nome que você inventa para guardar um valor | `idade`, `nome`, `media` |
| `PALAVRA_RESERVADA` | Palavra que o Python reserva para si. Não pode ser usada como nome | `and`, `or`, `not`, `None` |
| `LITERAL_INTEIRO` | Número sem ponto | `17` |
| `LITERAL_REAL` | Número com ponto (em Python, o ponto é a "vírgula" decimal) | `1.75` |
| `LITERAL_STRING` | Texto entre aspas | `"Ana"` |
| `LITERAL_BOOLEANO` | Verdadeiro ou falso | `True`, `False` |
| `OPERADOR` | Faz uma conta, uma comparação ou uma atribuição | `+`, `>=`, `=` |
| `DELIMITADOR` | Separa ou agrupa | `(`, `)`, `,` |
| `NOVA_LINHA` (↵) | O fim de um comando | |

> **Curiosidade:** em C e em Java, cada comando termina com `;`. Em Python, quem termina o comando é a
> **quebra de linha**. Por isso ela vira um token (↵). Uma linha em branco ou só com comentário não
> termina comando nenhum, e por isso não gera ↵.

## 5. Desafio: `>=` é um token ou dois?

Escolha o exemplo **"5. Operadores e expressões"**, analise e procure `>=` na tabela.

O scanner leu `>=` como **um token só** (*operador relacional: maior ou igual*), e não como `>`
seguido de `=`. A regra é: quando dá para formar um token maior, o scanner fica com o maior. Teste
você mesmo: apague o espaço e escreva `a>=b`. O resultado é o mesmo.

## 6. Quando o scanner encontra um erro

Escolha **"7. Vários erros léxicos"** e analise. Aparecem três erros:

| Mensagem | O que significa | Como corrigir |
| --- | --- | --- |
| `Erro léxico na linha 1, coluna 9: número malformado '10.5.2'` | Um número só pode ter um ponto decimal | `preco = 10.52` |
| `Erro léxico na linha 2, coluna 12: caractere não reconhecido '@'` | `@` não faz parte do subconjunto | Para guardar um e-mail, use texto: `email = "ana@escola"` (dentro das aspas pode tudo) |
| `Erro léxico na linha 3, coluna 9: número malformado '12abc'` | Um número não pode vir colado a letras, e um nome não pode começar com dígito | `total = 12` ou `total = abc12` |

Como ler a mensagem:
- **linha** é a linha do código, começando em 1;
- **coluna** é a posição na linha, contando cada caractere (inclusive espaços), também a partir de 1.

O trecho com problema também fica **sublinhado em vermelho** no código colorido.

Repare que o scanner **não parou no primeiro erro**: ele continuou lendo e mostrou os três de uma vez.
Os pedaços certos (`preco`, `=`, `email`...) continuam aparecendo na tabela.

Outro erro comum é esquecer de fechar as aspas. Veja o exemplo **"4. Erro intencional"**:

```
Erro léxico na linha 1, coluna 8: string não fechada "Ana. Toda string precisa terminar com a
mesma aspa (") na mesma linha.
```

## 7. O que o scanner **não** verifica

O scanner só reconhece os pedaços. Ele **não** sabe se os pedaços formam um comando que faz sentido.
Digite e analise:

```python
= = 17 idade
```

Não aparece nenhum erro léxico, porque `=`, `=`, `17` e `idade` são todos tokens válidos. Mas isso
não é um comando Python que faça sentido! Verificar a **ordem** dos tokens é trabalho da próxima
fase, a **análise sintática**. Repare que, logo abaixo do resumo léxico (verde), aparece o resumo
sintático (amarelo), com um erro: *"um comando não pode começar com '='"*.

## 8. A segunda fase: o parser monta uma árvore

Depois do scanner vem o **parser** (analisador sintático). O scanner reconhece as "palavras"; o parser
verifica se elas formam "frases" válidas e organiza o programa numa **árvore**.

Para isso ele segue uma **gramática**: um conjunto de regras que diz quais sequências de tokens são
permitidas. Uma regra se lê assim:

```
soma = termo { ( "+" | "-" ) termo }
```

"Uma *soma* é um *termo*, seguido de zero ou mais vezes (`{ }`) um `+` ou um `-` e outro *termo*." A
gramática completa do projeto tem 15 regras e está em [gramatica.md](gramatica.md).

### Mão na massa: por que `10 + 5 * 2` dá 20, e não 30?

1. Escolha o exemplo **"8. Precedência: 10 + 5 * 2"** e clique em **Analisar**.
2. Desça até **Árvore sintática**. Veja a primeira atribuição:

```
■ Atribuição: resultado = …
├── ● Identificador: resultado
└── ◆ Adição (+)
    ├── ● Inteiro: 10
    └── ◆ Multiplicação (*)
        ├── ● Inteiro: 5
        └── ● Inteiro: 2
```

A **multiplicação está abaixo da adição**. Numa árvore, o que está embaixo é calculado primeiro:
primeiro `5 * 2 = 10`, depois `10 + 10 = 20`. É isso que significa "a multiplicação tem precedência
maior".

3. Clique no nó **Multiplicação**. O trecho `5 * 2` fica destacado em azul no código, e o quadro
   "Nó selecionado" mostra a regra que o reconheceu.
4. Em **Construção passo a passo**, clique em **Próximo ▶** várias vezes. Os nós aparecem na ordem em
   que o parser os cria: primeiro os números, depois a multiplicação, só depois a adição e, por
   último, o programa inteiro.
5. Veja agora a terceira linha, `(10 + 5) * 2`: os parênteses trocaram de lugar a adição e a
   multiplicação na árvore. E os parênteses em si **não aparecem** na AST: a própria forma da árvore
   já diz o que vem primeiro.

### AST e árvore de derivação

Clique na aba **Árvore de derivação**. Ela mostra **todas** as regras que o parser usou, com todos os
tokens, inclusive os parênteses e o fim de linha. Um simples `10` passa por 11 regras até virar folha!
A **AST** é o resumo, só com o que importa para o significado. Compare a contagem no topo:
*"AST: 22 nós · Árvore de derivação: 105 nós"*.

### Quando o parser encontra um erro

Escolha **"10. Vários erros sintáticos"** e analise. O parser mostra **quatro** erros, um por linha:
quando encontra um erro, ele pula até o fim da linha e continua no comando seguinte.

| Mensagem | O que significa | Como corrigir |
| --- | --- | --- |
| `depois de '+' era esperado um valor` | A conta ficou pela metade | `x = 5 + 1` |
| `depois de '=' era esperado um valor (...), mas foi encontrado o operador '*'` | Falta o primeiro valor da multiplicação | `y = 3 * 2` |
| `este ')' está sobrando` | Há mais `)` do que `(` | `z = (1 + 2)` |
| `só um nome (identificador) pode receber um valor com '='` | O `=` guarda o valor da direita no nome da esquerda, e `17` não é um nome | `idade = 17` |

Cada erro também mostra o que o parser **encontrou**, o que ele **esperava** e a **regra** da gramática
que não foi respeitada. O ponto do erro fica sublinhado em laranja no código.

> **Erro léxico ou sintático?** O erro **léxico** é uma "palavra" que não existe (`@`, `10.5.2`). O
> **sintático** é um conjunto de palavras válidas numa ordem que não forma uma frase (`x = 5 +`). Na
> tela, cada grupo tem o seu selo: **Léxico** ou **Sintático**.

## 9. Exercícios

1. Escreva `nota = 7.5` e `nota = "7.5"`. Quais categorias o `7.5` recebe em cada caso?
2. Quantos tokens tem `print("Oi", nome)`? Conte antes de analisar e depois confira.
3. Por que `# total = 10` não gera nenhum token?
4. Escreva `ligado = true` (com `t` minúsculo). Que categoria o `true` recebe? Por quê?
5. Escreva um código com **exatamente dois** erros léxicos diferentes e confira se o scanner encontra
   os dois.
6. Desenhe no papel a AST de `x = 20 - 5 - 3`. A subtração de cima é `20 - (5 - 3)` ou `(20 - 5) - 3`?
   Analise e confira.
7. Qual a diferença entre `2 + 3 * 4` e `(2 + 3) * 4` na árvore? E no resultado da conta?
8. Por que `x = 5 +` é um erro **sintático**, e não léxico?

<details>
<summary>Respostas</summary>

1. Em `nota = 7.5`, o `7.5` é um `LITERAL_REAL` (tipo float). Em `nota = "7.5"`, o `"7.5"` é um
   `LITERAL_STRING` (tipo str).
2. São 7: `print`, `(`, `"Oi"`, `,`, `nome`, `)` e o fim de linha (↵).
3. Porque tudo depois de `#` é comentário, e o scanner descarta comentários.
4. `IDENTIFICADOR`. O Python diferencia maiúsculas de minúsculas: só `True` é booleano, e `true` é
   um nome qualquer.
5. Por exemplo, `x = 1.2.3 $`: um número malformado e um caractere não reconhecido.
6. `(20 - 5) - 3`, que dá 12. A subtração de dentro (mais embaixo) é `20 - 5`: o `-` junta pela
   esquerda.
7. Em `2 + 3 * 4`, a multiplicação fica embaixo (14). Em `(2 + 3) * 4`, a adição fica embaixo (20).
8. Porque todos os tokens (`x`, `=`, `5`, `+`) existem. O problema é a **ordem**: depois de `+` a
   gramática exige um valor, e o comando acabou.

</details>
