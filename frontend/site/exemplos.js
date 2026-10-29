// Programas de exemplo, todos dentro do subconjunto do projeto.
// Os exemplos 4 e 7 têm erros léxicos de propósito.
const EXEMPLOS = [
  {
    titulo: "1. Números: inteiro e float",
    codigo: "idade = 17\naltura = 1.75",
  },
  {
    titulo: "2. Strings: 17 é diferente de \"17\"",
    codigo: "idade = 17\nidade_texto = \"17\"\nnome = \"Ana\"",
  },
  {
    titulo: "3. Booleanos e nomes",
    codigo: "aprovado = True\npendente = False\nsituacao = aprovado",
  },
  {
    titulo: "4. Erro intencional: string não fechada",
    codigo: "nome = \"Ana",
  },
  {
    titulo: "5. Operadores e expressões",
    codigo: "idade = 17\nproxima = idade + 1\nmaior = idade >= 18 and not False",
  },
  {
    titulo: "6. Comentários e print",
    codigo: "# média\nnota1 = 7.5\nmedia = (nota1 + 9) / 2  # divisão\nprint(\"Média:\", media)",
  },
  {
    titulo: "7. Vários erros léxicos",
    codigo: "preco = 10.5.2\nemail = ana@escola\ntotal = 12abc",
  },
];
