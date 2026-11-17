"""Analisador sintático (parser) do subconjunto de Python usado no projeto.

Estratégia: descendente recursivo escrito à mão. Cada não terminal da gramática
(docs/gramatica.md) vira uma função com o mesmo nome. A função consome os tokens
que pertencem à construção e devolve dois nós:

- o nó da AST (árvore sintática abstrata): só o que importa para o significado;
- o nó da árvore de derivação (concreta): todos os não terminais e terminais
  usados, inclusive parênteses e a NOVA_LINHA.

Erros: ao encontrar um erro, o parser registra uma mensagem didática e pula
até o fim da linha (modo pânico). Assim mostra um erro por comando, sem cascata.

Uso:
    tokens, _ = analisar_lexico("x = 1 + 2")
    ast, derivacao, erros = analisar_sintaxe(tokens)
"""

# ---------- Gramática (uma regra por não terminal) ----------

REGRAS = {
    "programa": "programa = { comando NOVA_LINHA }",
    "comando": "comando = atribuicao | expressao",
    "atribuicao": 'atribuicao = IDENTIFICADOR "=" expressao',
    "expressao": "expressao = disjuncao",
    "disjuncao": 'disjuncao = conjuncao { "or" conjuncao }',
    "conjuncao": 'conjuncao = negacao { "and" negacao }',
    "negacao": 'negacao = "not" negacao | comparacao',
    "comparacao": 'comparacao = soma [ ( "==" | "!=" | "<" | ">" | "<=" | ">=" ) soma ]',
    "soma": 'soma = termo { ( "+" | "-" ) termo }',
    "termo": 'termo = unario { ( "*" | "/" | "//" | "%" ) unario }',
    "unario": 'unario = ( "+" | "-" ) unario | potencia',
    "potencia": 'potencia = primario [ "**" unario ]',
    "primario": ("primario = LITERAL_INTEIRO | LITERAL_REAL | LITERAL_STRING | LITERAL_BOOLEANO"
                 ' | "None" | IDENTIFICADOR [ argumentos ] | "(" expressao ")"'),
    "argumentos": 'argumentos = "(" [ expressao { "," expressao } ] ")"',
}

# operador -> (tipo do nó, rótulo legível)
OPERADORES_SOMA = {"+": ("ADICAO", "Adição"), "-": ("SUBTRACAO", "Subtração")}
OPERADORES_TERMO = {
    "*": ("MULTIPLICACAO", "Multiplicação"),
    "/": ("DIVISAO", "Divisão"),
    "//": ("DIVISAO_INTEIRA", "Divisão inteira"),
    "%": ("RESTO", "Resto da divisão"),
}
OPERADORES_RELACIONAIS = {"==", "!=", "<", ">", "<=", ">="}
OPERADORES_UNARIOS = {"-": ("MENOS_UNARIO", "Menos unário"), "+": ("MAIS_UNARIO", "Mais unário")}

LITERAIS = {
    "LITERAL_INTEIRO": "Inteiro",
    "LITERAL_REAL": "Real",
    "LITERAL_STRING": "String",
    "LITERAL_BOOLEANO": "Booleano",
}

# Palavras reservadas que fazem parte do subconjunto; as outras (if, while...) ficam fora.
RESERVADAS_DO_SUBCONJUNTO = {"and", "or", "not", "None"}

ESPERADO_VALOR = ["número", "texto entre aspas", "True/False", "None", "nome", "("]

# Limites que mantêm a análise segura para entradas patológicas como "((((((...".
LIMITE_ANINHAMENTO = 100   # chamadas recursivas abertas ao mesmo tempo
LIMITE_ALTURA_AST = 250
LIMITE_ALTURA_DERIVACAO = 400


def analisar_sintaxe(tokens):
    """Devolve (ast, derivacao, erros). Se houver erro, ast e derivacao são None."""
    return _Parser(tokens).executar()


class ErroSintatico(Exception):
    def __init__(self, dados):
        super().__init__(dados["mensagem"])
        self.dados = dados


def _texto(token):
    """Como um token aparece numa mensagem para o aluno."""
    if token is None:
        return "o fim do código"
    if token["tipo"] == "NOVA_LINHA":
        return "o fim do código" if token["lexema"] == "" else "o fim da linha"
    return f"'{token['lexema']}'"


def _remover_alturas(raiz):
    pilha = [raiz]
    while pilha:
        no = pilha.pop()
        no.pop("_altura", None)
        pilha.extend(no.get("filhos", []))


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.erros = []
        self.proximo_id = 1
        self.aninhamento = 0
        self.parenteses_abertos = []  # tokens "(" ainda não fechados (para mensagens)

    # ---------- utilitários ----------

    def atual(self, deslocamento=0):
        i = self.pos + deslocamento
        return self.tokens[i] if i < len(self.tokens) else None

    def eh(self, lexema, deslocamento=0):
        token = self.atual(deslocamento)
        return (token is not None and token["lexema"] == lexema
                and token["tipo"] in ("OPERADOR", "DELIMITADOR", "PALAVRA_RESERVADA"))

    def consumir(self):
        token = self.atual()
        self.pos += 1
        return token

    def anterior(self):
        return self.tokens[self.pos - 1] if self.pos > 0 else None

    def no(self, tipo, rotulo, regra, inicio, filhos=(), atributos=None):
        """Cria um nó da AST cobrindo os tokens de `inicio` até o último consumido."""
        primeiro, ultimo = self.tokens[inicio], self.tokens[self.pos - 1]
        filhos = list(filhos)
        altura = 1 + max((f["_altura"] for f in filhos), default=0)
        if altura > LIMITE_ALTURA_AST:
            self.erro_limite(primeiro)
        no = {
            "id": self.proximo_id,
            "tipo": tipo,
            "rotulo": rotulo,
            "atributos": atributos or {},
            "regra": REGRAS[regra],
            "linha": primeiro["linha"],
            "coluna": primeiro["coluna"],
            "linhaFim": ultimo["linha"],
            "colunaFim": ultimo["coluna"] + max(len(ultimo["lexema"]), 1) - 1,
            "filhos": filhos,
            "_altura": altura,
        }
        self.proximo_id += 1
        return no

    def nt(self, simbolo, filhos):
        """Nó não terminal da árvore de derivação."""
        altura = 1 + max((f["_altura"] for f in filhos), default=0)
        if altura > LIMITE_ALTURA_DERIVACAO:
            self.erro_limite(self.atual() or self.anterior())
        return {"tipo": "NAO_TERMINAL", "simbolo": simbolo, "filhos": filhos, "_altura": altura}

    @staticmethod
    def terminal(token):
        return {
            "tipo": "TERMINAL",
            "simbolo": token["tipo"],
            "lexema": token["lexema"],
            "linha": token["linha"],
            "coluna": token["coluna"],
            "_altura": 1,
        }

    # ---------- erros ----------

    def erro(self, explicacao, esperado, regra, token=None):
        token = token if token is not None else self.atual()
        if token is None:  # acabaram os tokens: aponta logo depois do último
            ultimo = self.tokens[-1]
            linha, coluna = ultimo["linha"], ultimo["coluna"] + len(ultimo["lexema"])
        else:
            linha, coluna = token["linha"], token["coluna"]
        raise ErroSintatico({
            "tipo": "ERRO_SINTATICO",
            "linha": linha,
            "coluna": coluna,
            "encontrado": _texto(token),
            "esperado": esperado,
            "regra": REGRAS[regra],
            "mensagem": f"Erro sintático na linha {linha}, coluna {coluna}: {explicacao}",
        })

    def erro_limite(self, token):
        self.erro("a expressão está aninhada ou longa demais para ser analisada e desenhada. "
                  "Divida-a em comandos menores.", [], "expressao", token)

    def entrar(self, token):
        self.aninhamento += 1
        if self.aninhamento > LIMITE_ANINHAMENTO:
            self.erro_limite(token)

    def sair(self):
        self.aninhamento -= 1

    def sincronizar(self):
        """Modo pânico: descarta tokens até o fim da linha atual (inclusive)."""
        self.aninhamento = 0
        self.parenteses_abertos = []
        while self.pos < len(self.tokens):
            if self.consumir()["tipo"] == "NOVA_LINHA":
                return

    # ---------- programa e comandos ----------

    def executar(self):
        comandos_ast, comandos_der = [], []
        while self.pos < len(self.tokens):
            try:
                ast, der = self.comando()
                self.fim_do_comando(ast)
                comandos_ast.append(ast)
                comandos_der.extend([der, self.terminal(self.consumir())])
            except ErroSintatico as e:
                self.erros.append(e.dados)
                self.sincronizar()

        if self.erros:
            return None, None, self.erros

        programa = {
            "id": self.proximo_id,
            "tipo": "PROGRAMA",
            "rotulo": "Programa",
            "atributos": {"comandos": len(comandos_ast)},
            "regra": REGRAS["programa"],
            "linha": self.tokens[0]["linha"] if self.tokens else 1,
            "coluna": self.tokens[0]["coluna"] if self.tokens else 1,
            "linhaFim": comandos_ast[-1]["linhaFim"] if comandos_ast else 1,
            "colunaFim": comandos_ast[-1]["colunaFim"] if comandos_ast else 1,
            "filhos": comandos_ast,
        }
        derivacao = {"tipo": "NAO_TERMINAL", "simbolo": "programa", "filhos": comandos_der}
        _remover_alturas(programa)
        _remover_alturas(derivacao)
        return programa, derivacao, []

    def fim_do_comando(self, ast):
        """Depois de um comando completo, só pode vir a NOVA_LINHA."""
        token = self.atual()
        if token is not None and token["tipo"] == "NOVA_LINHA":
            return
        if self.eh("="):
            if ast["tipo"] == "ATRIBUICAO":
                self.erro("atribuição múltipla (como a = b = 1) não faz parte do subconjunto. "
                          "Faça uma atribuição por linha.", ["fim da linha"], "atribuicao")
            self.erro("só um nome (identificador) pode receber um valor com '='. "
                      "O lado esquerdo da atribuição deve ser um nome, como em idade = 17.",
                      ["fim da linha"], "atribuicao")
        if self.eh(")"):
            self.erro("este ')' está sobrando: não há nenhum '(' aberto para ele fechar.",
                      ["fim da linha"], "primario")
        self.erro(f"era esperado o fim do comando (quebra de linha) depois de {_texto(self.anterior())}, "
                  f"mas foi encontrado {_texto(token)}. Cada linha deve ter um único comando; "
                  "talvez falte um operador entre os dois valores.",
                  ["fim da linha"], "programa")

    def comando(self):
        token = self.atual()
        if token["tipo"] == "IDENTIFICADOR" and self.eh("=", 1):
            ast, der = self.atribuicao()
        else:
            if token["tipo"] == "PALAVRA_RESERVADA" and token["lexema"] not in RESERVADAS_DO_SUBCONJUNTO:
                self.erro(f"a palavra reservada {_texto(token)} não faz parte do subconjunto desta "
                          "ferramenta. Comandos com blocos (if, else, while, for, def...) ainda não "
                          "são suportados.", ["nome", "valor"], "comando")
            if self.eh("="):
                self.erro("um comando não pode começar com '='. Para guardar um valor, escreva o "
                          "nome antes: nome = valor.", ["nome", "valor"], "comando")
            ast, der = self.expressao()
        return ast, self.nt("comando", [der])

    def atribuicao(self):
        inicio = self.pos
        nome = self.consumir()
        alvo = self.no("IDENTIFICADOR", f"Identificador: {nome['lexema']}", "atribuicao",
                       inicio, atributos={"nome": nome["lexema"]})
        igual = self.consumir()
        valor, der_valor = self.expressao()
        ast = self.no("ATRIBUICAO", f"Atribuição: {nome['lexema']} = …", "atribuicao", inicio,
                      [alvo, valor], {"nome": nome["lexema"]})
        der = self.nt("atribuicao", [self.terminal(nome), self.terminal(igual), der_valor])
        return ast, der

    # ---------- expressões, da menor para a maior precedência ----------

    def expressao(self):
        self.entrar(self.atual())
        ast, der = self.disjuncao()
        self.sair()
        return ast, self.nt("expressao", [der])

    def binaria(self, simbolo, proximo, operadores):
        """Operadores binários associativos à esquerda: a op b op c = (a op b) op c."""
        inicio = self.pos
        ast, der = proximo()
        filhos_der = [der]
        while self.atual() is not None and self.atual()["lexema"] in operadores \
                and self.atual()["tipo"] in ("OPERADOR", "PALAVRA_RESERVADA"):
            op = self.consumir()
            direita, der_direita = proximo()
            tipo, rotulo = operadores[op["lexema"]]
            ast = self.no(tipo, f"{rotulo} ({op['lexema']})", simbolo, inicio,
                          [ast, direita], {"operador": op["lexema"]})
            filhos_der += [self.terminal(op), der_direita]
        return ast, self.nt(simbolo, filhos_der)

    def disjuncao(self):
        return self.binaria("disjuncao", self.conjuncao, {"or": ("OU_LOGICO", "Ou lógico")})

    def conjuncao(self):
        return self.binaria("conjuncao", self.negacao, {"and": ("E_LOGICO", "E lógico")})

    def negacao(self):
        if not self.eh("not"):
            ast, der = self.comparacao()
            return ast, self.nt("negacao", [der])
        inicio = self.pos
        op = self.consumir()
        self.entrar(op)
        operando, der_operando = self.negacao()
        self.sair()
        ast = self.no("NAO_LOGICO", "Não lógico (not)", "negacao", inicio, [operando], {"operador": "not"})
        return ast, self.nt("negacao", [self.terminal(op), der_operando])

    def eh_relacional(self):
        token = self.atual()
        return token is not None and token["tipo"] == "OPERADOR" and token["lexema"] in OPERADORES_RELACIONAIS

    def comparacao(self):
        inicio = self.pos
        ast, der = self.soma()
        filhos_der = [der]
        if self.eh_relacional():
            op = self.consumir()
            direita, der_direita = self.soma()
            ast = self.no("COMPARACAO", f"Comparação ({op['lexema']})", "comparacao", inicio,
                          [ast, direita], {"operador": op["lexema"]})
            filhos_der += [self.terminal(op), der_direita]
            if self.eh_relacional():
                self.erro("comparações encadeadas (como a < b < c) não fazem parte do subconjunto. "
                          "Use 'and': a < b and b < c.", ["fim da linha", "and", "or"], "comparacao")
        return ast, self.nt("comparacao", filhos_der)

    def soma(self):
        return self.binaria("soma", self.termo, OPERADORES_SOMA)

    def termo(self):
        return self.binaria("termo", self.unario, OPERADORES_TERMO)

    def unario(self):
        token = self.atual()
        self.entrar(token)
        if token is not None and token["tipo"] == "OPERADOR" and token["lexema"] in OPERADORES_UNARIOS:
            inicio = self.pos
            op = self.consumir()
            operando, der_operando = self.unario()
            tipo, rotulo = OPERADORES_UNARIOS[op["lexema"]]
            ast = self.no(tipo, f"{rotulo} ({op['lexema']})", "unario", inicio,
                          [operando], {"operador": op["lexema"]})
            der = self.nt("unario", [self.terminal(op), der_operando])
        else:
            ast, der_potencia = self.potencia()
            der = self.nt("unario", [der_potencia])
        self.sair()
        return ast, der

    def potencia(self):
        """Associativa à direita: 2 ** 3 ** 2 = 2 ** (3 ** 2)."""
        inicio = self.pos
        base, der_base = self.primario()
        if not self.eh("**"):
            return base, self.nt("potencia", [der_base])
        op = self.consumir()
        expoente, der_expoente = self.unario()
        ast = self.no("POTENCIA", "Potência (**)", "potencia", inicio, [base, expoente], {"operador": "**"})
        return ast, self.nt("potencia", [der_base, self.terminal(op), der_expoente])

    def primario(self):
        token = self.atual()
        inicio = self.pos

        if token is not None and token["tipo"] in LITERAIS:
            self.consumir()
            ast = self.no(token["tipo"], f"{LITERAIS[token['tipo']]}: {token['lexema']}", "primario",
                          inicio, atributos={"valor": token["lexema"]})
            return ast, self.nt("primario", [self.terminal(token)])

        if self.eh("None"):
            self.consumir()
            ast = self.no("LITERAL_NONE", "None", "primario", inicio, atributos={"valor": "None"})
            return ast, self.nt("primario", [self.terminal(token)])

        if token is not None and token["tipo"] == "IDENTIFICADOR":
            self.consumir()
            if self.eh("("):
                argumentos, der_argumentos = self.argumentos(token)
                ast = self.no("CHAMADA_FUNCAO", f"Chamada de função: {token['lexema']}(…)", "primario",
                              inicio, argumentos, {"nome": token["lexema"]})
                return ast, self.nt("primario", [self.terminal(token), der_argumentos])
            ast = self.no("IDENTIFICADOR", f"Identificador: {token['lexema']}", "primario", inicio,
                          atributos={"nome": token["lexema"]})
            return ast, self.nt("primario", [self.terminal(token)])

        if self.eh("("):
            abre = self.consumir()
            self.parenteses_abertos.append(abre)
            ast, der = self.expressao()
            if not self.eh(")"):
                self.erro(f"era esperado ')' para fechar o parêntese aberto na linha {abre['linha']}, "
                          f"coluna {abre['coluna']}, mas foi encontrado {_texto(self.atual())}.",
                          [")"], "primario")
            fecha = self.consumir()
            self.parenteses_abertos.pop()
            # Os parênteses só agrupam: não viram nó na AST, só na árvore de derivação.
            return ast, self.nt("primario", [self.terminal(abre), der, self.terminal(fecha)])

        self.erro_valor_esperado(token)

    def argumentos(self, nome):
        abre = self.consumir()
        self.parenteses_abertos.append(abre)
        asts, ders = [], [self.terminal(abre)]
        while not self.eh(")"):
            ast, der = self.expressao()
            asts.append(ast)
            ders.append(der)
            if self.eh(","):
                ders.append(self.terminal(self.consumir()))
                continue
            if not self.eh(")"):
                self.erro(f"era esperado ',' entre os argumentos ou ')' para fechar a chamada de "
                          f"'{nome['lexema']}' (aberta na linha {abre['linha']}, coluna {abre['coluna']}), "
                          f"mas foi encontrado {_texto(self.atual())}.", [",", ")"], "argumentos")
        ders.append(self.terminal(self.consumir()))
        self.parenteses_abertos.pop()
        return asts, self.nt("argumentos", ders)

    def erro_valor_esperado(self, token):
        """Monta a mensagem mais útil possível quando faltou um valor."""
        anterior = self.anterior()
        depois = f"depois de {_texto(anterior)} " if anterior is not None else ""

        if token is None:
            if self.parenteses_abertos:
                abre = self.parenteses_abertos[-1]
                self.erro(f"o código terminou antes de fechar o parêntese aberto na linha "
                          f"{abre['linha']}, coluna {abre['coluna']}.", [")"], "primario", None)
            self.erro(f"o código terminou no meio de uma expressão: {depois}era esperado um valor.",
                      ESPERADO_VALOR, "primario", None)

        if token["tipo"] == "NOVA_LINHA":
            self.erro(f"expressão incompleta: {depois}era esperado um valor, mas {_texto(token)} chegou "
                      "antes.", ESPERADO_VALOR, "primario")

        if token["lexema"] == "=" and anterior is not None and anterior["tipo"] == "OPERADOR":
            self.erro(f"operadores compostos como '{anterior['lexema']}=' não fazem parte do subconjunto. "
                      f"Em vez de x {anterior['lexema']}= 1, escreva x = x {anterior['lexema']} 1.",
                      ESPERADO_VALOR, "primario")

        if token["tipo"] == "OPERADOR":
            dica = (" Há dois operadores seguidos: entre eles precisa haver um valor."
                    if anterior is not None and anterior["tipo"] == "OPERADOR" else "")
            self.erro(f"{depois}era esperado um valor (número, texto, nome ou '('), mas foi encontrado "
                      f"o operador {_texto(token)}.{dica}", ESPERADO_VALOR, "primario")

        if token["lexema"] == ")":
            self.erro(f"{depois}era esperado um valor, mas foi encontrado ')'. "
                      "Não pode haver parênteses vazios nem um ')' sem valor antes dele.",
                      ESPERADO_VALOR, "primario")

        if token["tipo"] == "PALAVRA_RESERVADA":
            self.erro(f"a palavra reservada {_texto(token)} não pode ser usada como valor"
                      f"{' aqui' if token['lexema'] in RESERVADAS_DO_SUBCONJUNTO else ' e não faz parte do subconjunto'}.",
                      ESPERADO_VALOR, "primario")

        self.erro(f"{depois}era esperado um valor (número, texto, nome ou '('), mas foi encontrado "
                  f"{_texto(token)}.", ESPERADO_VALOR, "primario")
