"""Testes de interface: elementos da tela, edição do código e seleção de exemplos."""
import pytest
from playwright.sync_api import expect

# Mesmo conteúdo de frontend/site/exemplos.js. Se um exemplo mudar lá, este teste avisa.
EXEMPLOS = [
    ("0", "idade = 17\naltura = 1.75"),
    ("1", 'idade = 17\nidade_texto = "17"\nnome = "Ana"'),
    ("2", "aprovado = True\npendente = False\nsituacao = aprovado"),
    ("3", 'nome = "Ana'),
]


# ---------- Elementos da tela ----------

def test_identifica_o_sistema_e_a_linguagem(tela):
    expect(tela).to_have_title("Visualizador Léxico de Python")
    expect(tela.locator("h1")).to_have_text("Visualizador Léxico de Python")
    expect(tela.locator("#linguagem")).to_contain_text("Python")


def test_tem_campo_botao_resultado_e_seletor(tela):
    expect(tela.locator("textarea#codigo")).to_be_visible()
    expect(tela.locator("textarea#codigo")).to_be_editable()
    expect(tela.locator("button#analisar")).to_be_enabled()
    expect(tela.locator("button#analisar")).to_have_text("Analisar")
    expect(tela.locator("#resultado")).to_be_visible()
    expect(tela.locator("select#exemplos")).to_be_visible()


def test_campo_de_codigo_usa_fonte_monoespacada(tela):
    fonte = tela.locator("#codigo").evaluate("el => getComputedStyle(el).fontFamily")
    assert "monospace" in fonte


def test_seletor_tem_pelo_menos_tres_exemplos(tela):
    opcoes = tela.locator("#exemplos option:not([value=''])")
    expect(opcoes).to_have_count(len(EXEMPLOS))
    assert opcoes.count() >= 3


# ---------- Edição do código ----------

def test_digitar_codigo(tela):
    tela.locator("#codigo").fill("idade = 17")
    expect(tela.locator("#codigo")).to_have_value("idade = 17")


def test_editar_e_substituir_codigo(tela):
    campo = tela.locator("#codigo")
    campo.fill("idade = 17")
    campo.press("End")
    campo.type("\nnome = \"Ana\"")
    expect(campo).to_have_value('idade = 17\nnome = "Ana"')

    campo.fill("x = 1")
    expect(campo).to_have_value("x = 1")


def test_aceita_caracteres_especiais(tela):
    codigo = 'texto = "ação, coração 😀"\t# comentário {}'
    tela.locator("#codigo").fill(codigo)
    expect(tela.locator("#codigo")).to_have_value(codigo)


def test_codigo_permanece_apos_analisar(tela):
    tela.locator("#codigo").fill("idade = 17")
    tela.locator("#analisar").click()
    expect(tela.locator("#resultado")).to_have_class("sucesso")
    expect(tela.locator("#codigo")).to_have_value("idade = 17")


# ---------- Exemplos ----------

@pytest.mark.parametrize("valor, codigo", EXEMPLOS)
def test_cada_exemplo_carrega_seu_codigo(tela, valor, codigo):
    tela.locator("#exemplos").select_option(valor)
    expect(tela.locator("#codigo")).to_have_value(codigo)


def test_novo_exemplo_substitui_o_anterior(tela):
    tela.locator("#exemplos").select_option("0")
    tela.locator("#exemplos").select_option("2")
    expect(tela.locator("#codigo")).to_have_value(EXEMPLOS[2][1])


def test_exemplo_substitui_codigo_digitado(tela):
    tela.locator("#codigo").fill("codigo digitado antes")
    tela.locator("#exemplos").select_option("1")
    expect(tela.locator("#codigo")).to_have_value(EXEMPLOS[1][1])


def test_exemplo_pode_ser_editado(tela):
    tela.locator("#exemplos").select_option("0")
    campo = tela.locator("#codigo")
    campo.press("Control+End")
    campo.type("\nnome = \"Ana\"")
    expect(campo).to_have_value(EXEMPLOS[0][1] + '\nnome = "Ana"')


def test_opcao_vazia_nao_apaga_o_codigo(tela):
    tela.locator("#codigo").fill("x = 1")
    tela.locator("#exemplos").select_option("")
    expect(tela.locator("#codigo")).to_have_value("x = 1")


def test_selecionar_exemplo_nao_envia_requisicao(tela, chamadas_api):
    tela.locator("#exemplos").select_option("0")
    expect(tela.locator("#resultado")).to_have_text("O resultado da análise aparecerá aqui.")
    assert chamadas_api == []
