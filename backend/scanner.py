"""Analisador léxico (scanner) do subconjunto de Python usado no projeto.

O scanner lê o código caractere a caractere, agrupa os caracteres em lexemas
e classifica cada lexema numa categoria de token. Ele não verifica se o programa
faz sentido (isso é papel do parser, na Etapa 4): só reconhece as "palavras".

Uso:
    tokens, erros = analisar_lexico("idade = 17")
"""
import keyword

# ---------- Tabelas do subconjunto ----------

BOOLEANOS = {"True", "False"}

# Todas as palavras reservadas do Python, menos True/False (tratados como literais).
PALAVRAS_RESERVADAS = set(keyword.kwlist) - BOOLEANOS

DESCRICAO_PALAVRAS = {
    "and": "operador lógico E: só é verdadeiro se os dois lados forem verdadeiros",
    "or": "operador lógico OU: é verdadeiro se pelo menos um lado for verdadeiro",
    "not": "operador lógico NÃO: inverte o valor lógico",
    "None": "valor especial que representa a ausência de valor (tipo NoneType)",
}
DESCRICAO_PALAVRA_FORA = "palavra reservada do Python (fora do subconjunto desta ferramenta)"

# Ordem importa: os operadores de dois caracteres vêm antes dos de um,
# para que ">=" seja lido como um token só (regra do maior casamento).
OPERADORES = {
    "**": "operador aritmético: potência",
    "//": "operador aritmético: divisão inteira",
    "==": "operador relacional: igual a",
    "!=": "operador relacional: diferente de",
    "<=": "operador relacional: menor ou igual",
    ">=": "operador relacional: maior ou igual",
    "+": "operador aritmético: soma",
    "-": "operador aritmético: subtração",
    "*": "operador aritmético: multiplicação",
    "/": "operador aritmético: divisão",
    "%": "operador aritmético: resto da divisão",
    "=": "operador de atribuição: cola o nome ao valor",
    "<": "operador relacional: menor que",
    ">": "operador relacional: maior que",
}

DELIMITADORES = {
    "(": "delimitador: abre parênteses",
    ")": "delimitador: fecha parênteses",
    ",": "delimitador: separa itens",
}

DESCRICAO_TIPO = {
    "IDENTIFICADOR": "nome (identificador): uma etiqueta que aponta para um objeto",
    "LITERAL_INTEIRO": "número inteiro: vira um objeto do tipo int",
    "LITERAL_REAL": "número real: vira um objeto do tipo float",
    "LITERAL_STRING": "texto entre aspas: vira um objeto do tipo str",
    "LITERAL_BOOLEANO": "valor lógico: vira um objeto do tipo bool",
    "NOVA_LINHA": "fim da linha: em Python, a quebra de linha encerra o comando",
}

DIGITOS = "0123456789"
ESPACOS = " \t\r\f"


def analisar_lexico(codigo):
    """Devolve (tokens, erros). Cada item é um dicionário pronto para virar JSON."""
    return _Scanner(codigo).executar()


class _Scanner:
    def __init__(self, codigo):
        self.codigo = codigo
        self.i = 0          # posição atual no texto
        self.linha = 1      # linha e coluna do caractere atual (começam em 1)
        self.coluna = 1
        self.tokens = []
        self.erros = []
        self.parenteses = 0           # dentro de parênteses, a quebra de linha não encerra o comando
        self.linha_tem_token = False  # o comando atual já tem algum token?

    # ---------- utilitários ----------

    def atual(self, deslocamento=0):
        pos = self.i + deslocamento
        return self.codigo[pos] if pos < len(self.codigo) else ""

    def avancar(self, quantidade=1):
        """Anda no texto atualizando linha e coluna."""
        for _ in range(quantidade):
            if self.atual() == "\n":
                self.linha += 1
                self.coluna = 1
            else:
                self.coluna += 1
            self.i += 1

    def token(self, tipo, lexema, linha, coluna, descricao):
        self.tokens.append(
            {"tipo": tipo, "lexema": lexema, "linha": linha, "coluna": coluna, "descricao": descricao}
        )
        if tipo != "NOVA_LINHA":
            self.linha_tem_token = True

    def erro(self, lexema, linha, coluna, explicacao):
        self.erros.append({
            "tipo": "ERRO_LEXICO",
            "lexema": lexema,
            "linha": linha,
            "coluna": coluna,
            "mensagem": f"Erro léxico na linha {linha}, coluna {coluna}: {explicacao}",
        })

    def nova_linha(self, lexema):
        if self.linha_tem_token and self.parenteses == 0:
            self.token("NOVA_LINHA", lexema, self.linha, self.coluna, DESCRICAO_TIPO["NOVA_LINHA"])
            self.linha_tem_token = False

    # ---------- laço principal ----------

    def executar(self):
        while self.i < len(self.codigo):
            c = self.atual()
            if c == "\n":
                self.nova_linha("\n")
                self.avancar()
            elif c in ESPACOS:
                self.avancar()
            elif c == "#":
                self.ler_comentario()
            elif c.isalpha() or c == "_":
                self.ler_nome()
            elif c in DIGITOS or (c == "." and self.atual(1) in DIGITOS and self.atual(1) != ""):
                self.ler_numero()
            elif c in "\"'":
                self.ler_string()
            elif not self.ler_operador_ou_delimitador():
                self.erro(c, self.linha, self.coluna,
                          f"caractere não reconhecido '{c}'. "
                          "Verifique se ele faz parte do subconjunto suportado.")
                self.avancar()

        # O último comando também termina no fim do arquivo, mesmo sem "\n".
        self.nova_linha("")
        return self.tokens, self.erros

    # ---------- reconhecedores ----------

    def ler_comentario(self):
        # Comentário: do "#" até o fim da linha. É descartado (não vira token).
        while self.i < len(self.codigo) and self.atual() != "\n":
            self.avancar()

    def ler_nome(self):
        linha, coluna, inicio = self.linha, self.coluna, self.i
        while self.atual() and (self.atual().isalnum() or self.atual() == "_"):
            self.avancar()
        lexema = self.codigo[inicio:self.i]

        if lexema in BOOLEANOS:
            self.token("LITERAL_BOOLEANO", lexema, linha, coluna, DESCRICAO_TIPO["LITERAL_BOOLEANO"])
        elif lexema in PALAVRAS_RESERVADAS:
            descricao = DESCRICAO_PALAVRAS.get(lexema, DESCRICAO_PALAVRA_FORA)
            self.token("PALAVRA_RESERVADA", lexema, linha, coluna, descricao)
        else:
            self.token("IDENTIFICADOR", lexema, linha, coluna, DESCRICAO_TIPO["IDENTIFICADOR"])

    def ler_numero(self):
        linha, coluna, inicio = self.linha, self.coluna, self.i
        tipo = "LITERAL_INTEIRO"
        while self.atual() and self.atual() in DIGITOS:
            self.avancar()
        if self.atual() == ".":
            tipo = "LITERAL_REAL"
            self.avancar()
            while self.atual() and self.atual() in DIGITOS:
                self.avancar()

        # Número colado a letras, "_" ou outro ponto (12abc, 1.2.3): consome o trecho todo
        # e reporta um único erro, em vez de vários erros confusos.
        if self.atual() and (self.atual().isalnum() or self.atual() in "._"):
            while self.atual() and (self.atual().isalnum() or self.atual() in "._"):
                self.avancar()
            lexema = self.codigo[inicio:self.i]
            self.erro(lexema, linha, coluna,
                      f"número malformado '{lexema}'. Um número só pode ter dígitos e no máximo "
                      "um ponto decimal, e não pode vir colado a letras.")
            return

        self.token(tipo, self.codigo[inicio:self.i], linha, coluna, DESCRICAO_TIPO[tipo])

    def ler_string(self):
        linha, coluna, inicio = self.linha, self.coluna, self.i
        aspa = self.atual()

        # Strings com três aspas ficam fora do subconjunto: vira um erro só,
        # até as três aspas de fechamento (ou o fim do código).
        if self.codigo.startswith(aspa * 3, self.i):
            fim = self.codigo.find(aspa * 3, self.i + 3)
            fim = len(self.codigo) if fim == -1 else fim + 3
            self.avancar(fim - self.i)
            self.erro(aspa * 3, linha, coluna,
                      "strings com três aspas não fazem parte do subconjunto suportado.")
            return

        self.avancar()  # aspa de abertura
        while self.atual() and self.atual() != "\n":
            if self.atual() == "\\" and self.atual(1) not in ("", "\n"):
                self.avancar(2)  # sequência de escape, ex.: \" ou \n
            elif self.atual() == aspa:
                self.avancar()   # aspa de fechamento
                lexema = self.codigo[inicio:self.i]
                self.token("LITERAL_STRING", lexema, linha, coluna, DESCRICAO_TIPO["LITERAL_STRING"])
                return
            else:
                self.avancar()

        lexema = self.codigo[inicio:self.i].rstrip("\r")
        self.erro(lexema, linha, coluna,
                  f"string não fechada {lexema}. Toda string precisa terminar com a mesma "
                  f"aspa ({aspa}) na mesma linha.")

    def ler_operador_ou_delimitador(self):
        for simbolo, descricao in OPERADORES.items():
            if self.codigo.startswith(simbolo, self.i):
                self.token("OPERADOR", simbolo, self.linha, self.coluna, descricao)
                self.avancar(len(simbolo))
                return True

        c = self.atual()
        if c in DELIMITADORES:
            if c == "(":
                self.parenteses += 1
            elif c == ")":
                self.parenteses = max(0, self.parenteses - 1)
            self.token("DELIMITADOR", c, self.linha, self.coluna, DELIMITADORES[c])
            self.avancar()
            return True
        return False
