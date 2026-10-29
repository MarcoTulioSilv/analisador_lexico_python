"""Testes de ponta a ponta e de integração: navegador -> Nginx -> Flask -> tela.

Também cobre as validações e mensagens de erro exibidas ao usuário.
"""
import json

import pytest
from playwright.sync_api import expect

MSG_VAZIO = "Informe um código-fonte antes de solicitar a análise."
MSG_SEM_CONEXAO = "Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente."
MSG_INESPERADO = "Ocorreu um erro inesperado. Tente novamente mais tarde."


# ---------- Fluxo completo ----------

def test_digitar_e_analisar(tela):
    tela.locator("#codigo").fill("idade = 17")
    tela.locator("#analisar").click()
    resultado = tela.locator("#resultado")
    expect(resultado).to_have_class("sucesso")
    # Etapa 3: a resposta passou a ser a análise léxica (idade, =, 17 e o fim de linha).
    expect(resultado).to_have_text("Análise léxica concluída: 4 token(s) reconhecido(s).")


def test_envia_exatamente_o_codigo_do_campo(tela):
    codigo = 'texto = "ação 😀"\n\t# comentário {}'
    tela.locator("#codigo").fill(codigo)
    with tela.expect_request("**/api/analisar") as info:
        tela.locator("#analisar").click()
    assert json.loads(info.value.post_data) == {"codigo": codigo}
    expect(tela.locator("#resultado")).to_have_class("sucesso")


@pytest.mark.parametrize("valor", ["0", "1", "2", "4", "5"])
def test_exemplos_sem_erro_sao_tokenizados_com_sucesso(tela, valor):
    tela.locator("#exemplos").select_option(valor)
    tela.locator("#analisar").click()
    expect(tela.locator("#resultado")).to_have_class("sucesso")
    expect(tela.locator("#resultado")).to_contain_text("Análise léxica concluída")


@pytest.mark.parametrize("valor, quantidade", [("3", 1), ("6", 3)])
def test_exemplos_com_erro_intencional_mostram_os_erros(tela, valor, quantidade):
    tela.locator("#exemplos").select_option(valor)
    tela.locator("#analisar").click()
    expect(tela.locator("#resultado")).to_have_class("aviso")
    expect(tela.locator("#resultado")).to_contain_text(f"encontrou {quantidade} erro(s)")


def test_editar_exemplo_e_analisar(tela):
    tela.locator("#exemplos").select_option("0")  # 8 tokens
    campo = tela.locator("#codigo")
    campo.press("Control+End")
    campo.type("\nnome = \"Ana\"")  # + nome, =, "Ana" e mais um fim de linha
    tela.locator("#analisar").click()
    expect(tela.locator("#resultado")).to_contain_text("12 token(s)")


# ---------- Validação no navegador ----------

@pytest.mark.parametrize("codigo", ["", "   ", "\n\t  \n"])
def test_vazio_ou_espacos_nao_envia_e_orienta(tela, chamadas_api, codigo):
    tela.locator("#codigo").fill(codigo)
    tela.locator("#analisar").click()
    expect(tela.locator("#resultado")).to_have_text(MSG_VAZIO)
    expect(tela.locator("#resultado")).to_have_class("aviso")
    assert chamadas_api == []


def test_validacao_nao_bloqueia_entrada_valida_depois(tela):
    tela.locator("#analisar").click()
    expect(tela.locator("#resultado")).to_have_text(MSG_VAZIO)
    tela.locator("#codigo").fill("x = 1")
    tela.locator("#analisar").click()
    expect(tela.locator("#resultado")).to_have_class("sucesso")


# ---------- Erros vindos do backend ----------

def test_erro_de_entrada_do_backend_e_exibido(tela):
    # O navegador não checa o tamanho; quem recusa é o backend (validação no servidor).
    tela.locator("#codigo").fill("x" * 10_001)
    tela.locator("#analisar").click()
    expect(tela.locator("#resultado")).to_have_text("O código excede o limite de 10.000 caracteres.")
    expect(tela.locator("#resultado")).to_have_class("aviso")


def test_falha_de_comunicacao(tela):
    tela.route("**/api/analisar", lambda rota: rota.abort())
    tela.locator("#codigo").fill("idade = 17")
    tela.locator("#analisar").click()

    expect(tela.locator("#resultado")).to_have_text(MSG_SEM_CONEXAO)
    expect(tela.locator("#resultado")).to_have_class("erro")
    # A interface não fica travada e o código não se perde.
    expect(tela.locator("#analisar")).to_be_enabled()
    expect(tela.locator("#analisar")).to_have_text("Analisar")
    expect(tela.locator("#codigo")).to_have_value("idade = 17")


def test_recupera_apos_falha_de_comunicacao(tela):
    tela.route("**/api/analisar", lambda rota: rota.abort())
    tela.locator("#codigo").fill("idade = 17")
    tela.locator("#analisar").click()
    expect(tela.locator("#resultado")).to_have_text(MSG_SEM_CONEXAO)

    tela.unroute("**/api/analisar")
    tela.locator("#analisar").click()
    expect(tela.locator("#resultado")).to_have_class("sucesso")


def test_erro_interno_do_servidor(tela):
    tela.route(
        "**/api/analisar",
        lambda rota: rota.fulfill(status=500, content_type="text/html", body="<h1>Traceback ...</h1>"),
    )
    tela.locator("#codigo").fill("idade = 17")
    tela.locator("#analisar").click()
    expect(tela.locator("#resultado")).to_have_text(MSG_INESPERADO)
    expect(tela.locator("#resultado")).not_to_contain_text("Traceback")
    expect(tela.locator("#analisar")).to_be_enabled()


def test_botao_desabilitado_durante_envio(tela):
    # Segura a resposta para observar o estado intermediário do botão.
    rotas = []
    tela.route("**/api/analisar", lambda rota: rotas.append(rota))
    tela.locator("#codigo").fill("idade = 17")
    tela.locator("#analisar").click()

    expect(tela.locator("#analisar")).to_be_disabled()
    expect(tela.locator("#analisar")).to_have_text("Enviando...")

    rotas[0].continue_()
    expect(tela.locator("#analisar")).to_be_enabled()
    expect(tela.locator("#resultado")).to_have_class("sucesso")


def test_falha_de_comunicacao_esconde_analise_anterior(tela):
    # Depois de uma análise bem-sucedida, uma falha não pode deixar a tabela antiga
    # na tela como se fosse o resultado do código atual.
    tela.locator("#codigo").fill("idade = 17")
    tela.locator("#analisar").click()
    expect(tela.locator("#analise")).to_be_visible()

    tela.route("**/api/analisar", lambda rota: rota.abort())
    tela.locator("#codigo").fill("outro = 1")
    tela.locator("#analisar").click()
    expect(tela.locator("#resultado")).to_have_text(MSG_SEM_CONEXAO)
    expect(tela.locator("#analise")).to_be_hidden()
