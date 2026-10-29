"""Testes de interface da análise léxica (Etapa 3): tabela, cores, contagem,
erros, passo a passo, robustez e celular. Também gera os prints de evidência."""
import os

import pytest
from playwright.sync_api import expect

from conftest import PASTA_EVIDENCIAS


def analisar(tela, codigo=None, exemplo=None):
    if exemplo is not None:
        tela.locator("#exemplos").select_option(exemplo)
    else:
        tela.locator("#codigo").fill(codigo)
    tela.locator("#analisar").click()
    expect(tela.locator("#analise")).to_be_visible()


def linhas_da_tabela(tela):
    """Cada linha da tabela como (tipo, lexema, linha, coluna)."""
    return [
        tuple(linha.locator("td").nth(i).inner_text() for i in (1, 2, 3, 4))
        for linha in tela.locator("#tabela-tokens tbody tr").all()
    ]


# ---------- Tabela de tokens ----------

def test_tabela_mostra_tipo_lexema_e_posicao(tela):
    analisar(tela, 'idade = 17\nnome = "Ana"')
    assert linhas_da_tabela(tela) == [
        ("IDENTIFICADOR", "idade", "1", "1"),
        ("OPERADOR", "=", "1", "7"),
        ("LITERAL_INTEIRO", "17", "1", "9"),
        ("NOVA_LINHA", "↵ (quebra de linha)", "1", "11"),
        ("IDENTIFICADOR", "nome", "2", "1"),
        ("OPERADOR", "=", "2", "6"),
        ("LITERAL_STRING", '"Ana"', "2", "8"),
        ("NOVA_LINHA", "(fim do código)", "2", "13"),
    ]


def test_tabela_mostra_descricao_didatica(tela):
    analisar(tela, "17")
    expect(tela.locator("#tabela-tokens tbody tr").first).to_contain_text("vira um objeto do tipo int")


def test_tabela_tem_cabecalho_completo(tela):
    analisar(tela, "x = 1")
    expect(tela.locator("#tabela-tokens thead th")).to_have_text(
        ["#", "Tipo", "Lexema", "Linha", "Coluna", "Descrição"]
    )


# ---------- Código colorido e contagem ----------

def test_codigo_colorido_tem_um_elemento_por_token(tela):
    analisar(tela, "maior = idade >= 18 and not False")
    colorido = tela.locator("#codigo-colorido")
    expect(colorido.locator(".tk")).to_have_count(9)  # 8 tokens + fim de linha
    expect(colorido.locator(".tk-OPERADOR")).to_have_text(["=", ">="])
    expect(colorido.locator(".tk-PALAVRA_RESERVADA")).to_have_text(["and", "not"])
    expect(colorido.locator(".tk-LITERAL_BOOLEANO")).to_have_text("False")


def test_codigo_colorido_preserva_o_texto_original(tela):
    codigo = '# média\nnota = (7.5 + 9) / 2  # divisão\nprint("Média:", nota)'
    analisar(tela, codigo)
    # Removendo as marcas de fim de linha (↵), o texto é exatamente o código digitado.
    texto = tela.locator("#codigo-colorido").inner_text().replace("↵", "")
    assert texto == codigo


def test_codigo_colorido_alinha_com_acentos_e_emoji(tela):
    analisar(tela, 'é = "😀" + ação')
    expect(tela.locator("#codigo-colorido .tk-IDENTIFICADOR")).to_have_text(["é", "ação"])
    expect(tela.locator("#codigo-colorido .tk-LITERAL_STRING")).to_have_text('"😀"')


def test_contagem_por_categoria(tela):
    analisar(tela, "a = 1\nb = a + 2")
    chips = tela.locator("#contagem .chip")
    expect(chips).to_have_text([
        "IDENTIFICADOR × 3", "OPERADOR × 3", "LITERAL_INTEIRO × 2", "NOVA_LINHA × 2",
    ])


# ---------- Erros léxicos ----------

def test_erros_do_exemplo_7_com_linha_e_coluna(tela):
    analisar(tela, exemplo="6")
    expect(tela.locator("#secao-erros")).to_be_visible()
    erros = tela.locator("#lista-erros li")
    expect(erros).to_have_count(3)
    expect(erros.nth(0)).to_contain_text("Erro léxico na linha 1, coluna 9: número malformado '10.5.2'")
    expect(erros.nth(1)).to_contain_text("Erro léxico na linha 2, coluna 12: caractere não reconhecido '@'")
    expect(erros.nth(2)).to_contain_text("Erro léxico na linha 3, coluna 9: número malformado '12abc'")


def test_erros_aparecem_destacados_no_codigo(tela):
    analisar(tela, "x = 1 @ 2")
    expect(tela.locator("#codigo-colorido .tk-erro")).to_have_text("@")
    # Os tokens válidos continuam aparecendo.
    expect(tela.locator("#codigo-colorido .tk-LITERAL_INTEIRO")).to_have_text(["1", "2"])


def test_string_nao_fechada(tela):
    analisar(tela, exemplo="3")
    expect(tela.locator("#lista-erros li")).to_contain_text("string não fechada")
    expect(tela.locator("#codigo-colorido .tk-erro")).to_have_text('"Ana')


def test_secao_de_erros_some_quando_nao_ha_erros(tela):
    analisar(tela, "x @")
    expect(tela.locator("#secao-erros")).to_be_visible()
    analisar(tela, "x = 1")
    expect(tela.locator("#secao-erros")).to_be_hidden()


@pytest.mark.parametrize(
    "codigo",
    ['@@@ $$$ ??? """', "!!!\n;;;\n[]{}", '"""\nsem fim', "1.2.3.4.5abc", "\\\\\\", "x = (((", ")))"],
)
def test_entrada_invalida_nao_quebra_a_interface(tela, codigo):
    erros_js = []
    tela.on("pageerror", lambda erro: erros_js.append(erro))
    analisar(tela, codigo)
    expect(tela.locator("#resultado")).not_to_have_class("erro")
    expect(tela.locator("#analisar")).to_be_enabled()
    assert erros_js == []
    # E a tela continua funcionando depois.
    analisar(tela, "x = 1")
    expect(tela.locator("#resultado")).to_have_class("sucesso")


def test_codigo_com_html_aparece_como_texto(tela):
    analisar(tela, 'x = "<b>negrito</b>" # <script>alert(1)</script>')
    expect(tela.locator("#codigo-colorido b")).to_have_count(0)
    expect(tela.locator("#codigo-colorido script")).to_have_count(0)
    expect(tela.locator("#codigo-colorido .tk-LITERAL_STRING")).to_have_text('"<b>negrito</b>"')


def test_so_comentario_nao_tem_tokens(tela):
    analisar(tela, "# só um comentário")
    expect(tela.locator("#resultado")).to_have_text("Análise léxica concluída: 0 token(s) reconhecido(s).")
    expect(tela.locator("#tabela-tokens tbody tr")).to_have_count(0)
    expect(tela.locator("#passo-explicacao")).to_contain_text("Nenhum token")


# ---------- Passo a passo ----------

def test_passo_a_passo_avanca_volta_e_destaca(tela):
    analisar(tela, "idade = 17")
    explicacao = tela.locator("#passo-explicacao")
    expect(explicacao).to_contain_text("reconheceu 4 token(s)")
    expect(tela.locator("#passo-anterior")).to_be_disabled()

    tela.locator("#passo-proximo").click()
    expect(explicacao).to_have_text(
        "Passo 1 de 4: o scanner leu idade na linha 1, coluna 1 → IDENTIFICADOR "
        "(nome (identificador): uma etiqueta que aponta para um objeto)."
    )
    expect(tela.locator("#codigo-colorido .atual")).to_have_text("idade")
    expect(tela.locator("#tabela-tokens tr.atual td").nth(2)).to_have_text("idade")

    tela.locator("#passo-proximo").click()
    tela.locator("#passo-proximo").click()
    expect(explicacao).to_contain_text("Passo 3 de 4: o scanner leu 17")
    expect(tela.locator("#codigo-colorido .atual")).to_have_text("17")

    tela.locator("#passo-anterior").click()
    expect(tela.locator("#codigo-colorido .atual")).to_have_text("=")
    expect(tela.locator(".atual")).to_have_count(2)  # um no código, um na tabela


def test_passo_a_passo_para_no_ultimo_token(tela):
    analisar(tela, "x")
    tela.locator("#passo-proximo").click()
    tela.locator("#passo-proximo").click()
    expect(tela.locator("#passo-explicacao")).to_contain_text("Passo 2 de 2: o scanner leu (fim do código)")
    expect(tela.locator("#passo-proximo")).to_be_disabled()


def test_reproduzir_percorre_todos_os_tokens(tela):
    analisar(tela, "x = 1")
    tela.locator("#passo-reproduzir").click()
    expect(tela.locator("#passo-reproduzir")).to_have_text("⏸ Pausar")
    expect(tela.locator("#passo-explicacao")).to_contain_text("Passo 4 de 4", timeout=8000)
    expect(tela.locator("#passo-reproduzir")).to_have_text("▶ Reproduzir")


def test_pausar_interrompe_a_reproducao(tela):
    analisar(tela, "a = 1 + 2 + 3 + 4 + 5")
    tela.locator("#passo-reproduzir").click()
    expect(tela.locator("#passo-explicacao")).to_contain_text("Passo 1 de")
    tela.locator("#passo-reproduzir").click()
    texto = tela.locator("#passo-explicacao").inner_text()
    tela.wait_for_timeout(2000)
    expect(tela.locator("#passo-explicacao")).to_have_text(texto)


def test_nova_analise_reinicia_o_passo_a_passo(tela):
    analisar(tela, "x = 1")
    tela.locator("#passo-proximo").click()
    analisar(tela, "y = 2")
    expect(tela.locator(".atual")).to_have_count(0)
    expect(tela.locator("#passo-explicacao")).to_contain_text("reconheceu 4 token(s)")


# ---------- Explicação didática ----------

def test_explicacao_de_token_e_lexema(tela):
    expect(tela.locator("#o-que-e summary")).to_have_text("O que é token e lexema?")
    tela.locator("#o-que-e summary").click()
    expect(tela.locator("#o-que-e")).to_contain_text("Lexema é o texto exato")


# ---------- Celular ----------

def test_celular_sem_rolagem_horizontal(tela):
    tela.set_viewport_size({"width": 375, "height": 740})
    analisar(tela, exemplo="5")
    largura_pagina = tela.evaluate("document.documentElement.scrollWidth")
    assert largura_pagina <= 375
    expect(tela.locator("#tabela-tokens")).to_be_attached()


# ---------- Evidências (prints) ----------

def salvar_print(tela, nome):
    os.makedirs(PASTA_EVIDENCIAS, exist_ok=True)
    tela.screenshot(path=os.path.join(PASTA_EVIDENCIAS, nome), full_page=True)


def test_gera_print_da_interface(tela):
    tela.set_viewport_size({"width": 1000, "height": 800})
    analisar(tela, exemplo="4")
    for _ in range(14):  # para no ">=" para mostrar o destaque do passo a passo
        tela.locator("#passo-proximo").click()
    expect(tela.locator("#codigo-colorido .atual")).to_have_text(">=")
    salvar_print(tela, "interface.png")


def test_gera_print_dos_erros_lexicos(tela):
    tela.set_viewport_size({"width": 1000, "height": 800})
    analisar(tela, exemplo="6")
    expect(tela.locator("#lista-erros li")).to_have_count(3)
    salvar_print(tela, "erros-lexicos.png")


def test_gera_print_no_celular(tela):
    tela.set_viewport_size({"width": 375, "height": 740})
    analisar(tela, exemplo="1")
    salvar_print(tela, "celular.png")
