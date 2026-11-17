# Fluxograma do funcionamento

Este é o fluxo de uma análise, do código digitado na interface até as vistas
preenchidas na tela. A decisão de projeto que o diagrama registra é a do losango:
**o parser roda mesmo quando a análise léxica encontrou erro**, sobre os tokens
que foram reconhecidos. O aluno vê os dois tipos de erro de uma vez, em vez de
corrigir um erro léxico só para descobrir, na execução seguinte, que ainda havia
um erro de estrutura.

Caixas em verde são as etapas que já existem (Etapas 1 a 3). Em âmbar, o que a
Etapa 4 acrescenta. Em cinza tracejado, o que fica fora deste escopo.

```mermaid
flowchart TD
    A["Aluno digita o código<br/>na área de texto"] --> B["POST /api/analisar<br/>validação da entrada"]
    B -->|"entrada inválida"| X["HTTP 400<br/>mensagem explicativa"]
    B -->|"entrada válida"| C["Análise léxica<br/>(scanner)"]
    C --> D{"Houve erro<br/>léxico?"}
    D -->|"sim"| E["Lista de erros léxicos<br/>linha, coluna e explicação"]
    D -->|"em todo caso"| F["Análise sintática<br/>(parser descendente recursivo)"]
    E -.->|"em todo caso"| F
    F --> K["Comandos com erro léxico<br/>são pulados (linhas_ignoradas)"]
    K --> G["AST, árvore de derivação<br/>e lista de erros sintáticos"]
    G --> H["Resposta JSON<br/>tokens, erros, ast, derivacao,<br/>erros_sintaticos, linhas_ignoradas"]
    H --> I["Três vistas sincronizadas:<br/>código colorido, tabela de tokens e árvore"]
    I -.-> J["Análise semântica<br/>(Etapa 5, fora deste escopo)"]

    classDef existente fill:#dcfce7,stroke:#15803d,color:#14532d
    classDef nova fill:#fef3c7,stroke:#b45309,color:#78350f
    classDef fora fill:#f4f4f5,stroke:#a1a1aa,color:#52525b,stroke-dasharray: 5 5

    class A,B,C,D,E,X existente
    class F,K,G,H,I nova
    class J fora
```

## Legenda

| Cor | Significado |
| --- | --- |
| Verde | Já implementado nas Etapas 1 a 3 |
| Âmbar | Acrescentado pela Etapa 4 (parser, AST, árvore na interface) |
| Cinza tracejado | Fora do escopo desta entrega |

## Observações sobre o fluxo

A validação da entrada acontece antes da análise léxica e é a única saída que
não produz tokens: campo ausente, código vazio ou acima de 10.000 caracteres
devolvem HTTP 400 com mensagem explicativa, sem chegar ao scanner.

A seta tracejada que sai dos erros léxicos para a análise sintática é a que
expressa a decisão de projeto: a lista de erros léxicos é acumulada e exibida,
mas não interrompe o pipeline. O parser recebe os tokens reconhecidos e tenta
construir a árvore a partir deles, recuperando-se dos erros em modo pânico
sincronizado em `NOVA_LINHA`.

Detalhe da implementação: o parser **pula os comandos que contêm um erro
léxico** (da primeira linha do comando até a sua `NOVA_LINHA`). Como o scanner
descarta o trecho inválido, `x = 1 @ 2` chegaria ao parser como `x = 1 2`, e ele
apontaria uma "falta de operador" que o aluno não cometeu. As linhas puladas
voltam no campo `linhas_ignoradas` e são avisadas na tela. Os demais comandos são
analisados normalmente (caso CT-27).

O campo `sucesso` da resposta passa, a partir desta etapa, a significar ausência
de erros léxicos **e** sintáticos. A mudança está registrada na seção de
mudanças entre etapas do README.
