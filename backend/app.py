from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from parser import analisar_sintaxe
from scanner import analisar_lexico
from validacao import validar_codigo

app = Flask(__name__)


@app.get("/api/saude")
def saude():
    return jsonify(status="ok")


@app.post("/api/analisar")
def analisar():
    dados = request.get_json(silent=True)
    codigo, erro = validar_codigo(dados)
    if erro:
        return jsonify(recebido=False, erro=erro), 400

    # Etapa 3: análise léxica. Erros léxicos não são erro da requisição (continua 200);
    # quem diz se o código passou é o campo "sucesso".
    tokens, erros = analisar_lexico(codigo)
    # Etapa 4: os campos acima continuam iguais; a análise sintática vem em "sintatico".
    return jsonify(sucesso=not erros, tokens=tokens, erros=erros, sintatico=analise_sintatica(tokens, erros))


MOTIVO_SEM_PARSER = (
    "A análise sintática não foi executada porque o código tem erros léxicos. "
    "Corrija-os primeiro: com tokens inválidos, o parser apontaria erros sem sentido."
)


def analise_sintatica(tokens, erros_lexicos):
    # Decisão de projeto: com erro léxico, o parser não roda.
    if erros_lexicos:
        return {"executado": False, "sucesso": False, "ast": None, "derivacao": None,
                "erros": [], "motivo": MOTIVO_SEM_PARSER}
    ast, derivacao, erros = analisar_sintaxe(tokens)
    return {"executado": True, "sucesso": not erros, "ast": ast, "derivacao": derivacao,
            "erros": erros, "motivo": None}


@app.errorhandler(Exception)
def erro_inesperado(erro):
    # Erros HTTP comuns (404, 405...) seguem o tratamento padrão do Flask.
    if isinstance(erro, HTTPException):
        return erro
    # Qualquer outra exceção: mensagem genérica, sem detalhes internos.
    app.logger.exception("Erro inesperado")
    return jsonify(recebido=False, erro="Erro interno no servidor. Tente novamente mais tarde."), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
