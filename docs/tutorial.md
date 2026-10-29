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
fase, a **análise sintática** (Etapa 4 do projeto).

## 8. Exercícios

1. Escreva `nota = 7.5` e `nota = "7.5"`. Quais categorias o `7.5` recebe em cada caso?
2. Quantos tokens tem `print("Oi", nome)`? Conte antes de analisar e depois confira.
3. Por que `# total = 10` não gera nenhum token?
4. Escreva `ligado = true` (com `t` minúsculo). Que categoria o `true` recebe? Por quê?
5. Escreva um código com **exatamente dois** erros léxicos diferentes e confira se o scanner encontra
   os dois.

<details>
<summary>Respostas</summary>

1. Em `nota = 7.5`, o `7.5` é um `LITERAL_REAL` (tipo float). Em `nota = "7.5"`, o `"7.5"` é um
   `LITERAL_STRING` (tipo str).
2. São 7: `print`, `(`, `"Oi"`, `,`, `nome`, `)` e o fim de linha (↵).
3. Porque tudo depois de `#` é comentário, e o scanner descarta comentários.
4. `IDENTIFICADOR`. O Python diferencia maiúsculas de minúsculas: só `True` é booleano, e `true` é
   um nome qualquer.
5. Por exemplo, `x = 1.2.3 $`: um número malformado e um caractere não reconhecido.

</details>
