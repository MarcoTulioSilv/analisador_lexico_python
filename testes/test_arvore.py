"""Testes de interface da análise sintática (Etapa 4): resumo, erros sintáticos,
AST navegável, árvore de derivação, construção passo a passo, consistência com
a tabela de tokens, entradas inválidas e celular. Também gera os prints."""
import os
import re

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


def no_ast(tela, tipo):
    return tela.locator(f"#arvore-ast .rotulo-no[data-tipo='{tipo}']")


# ---------- Resumo e árvore para código válido ----------

def test_arvore_aparece_para_codigo_valido(tela):  # CT-01
    analisar(tela, "idade = 17")
    expect(tela.locator("#resultado-sintatico")).to_have_text(
        "Análise sintática concluída: 1 comando(s) reconhecido(s).")
    expect(tela.locator("#resultado-sintatico")).to_have_class("sucesso")
    expect(tela.locator("#secao-arvore")).to_be_visible()
    expect(tela.locator("#arvore-ast .rotulo-no")).to_have_count(4)  # programa, atribuição, idade, 17
    expect(no_ast(tela, "ATRIBUICAO")).to_contain_text("Atribuição: idade = …")
    expect(no_ast(tela, "LITERAL_INTEIRO")).to_contain_text("Inteiro: 17")


def test_resumo_lexico_da_etapa_3_continua_igual(tela):
    analisar(tela, "idade = 17")
    expect(tela.locator("#resultado")).to_have_text("Análise léxica concluída: 4 token(s) reconhecido(s).")


def test_precedencia_aparece_na_arvore(tela):
    analisar(tela, exemplo="7")  # resultado = 10 + 5 * 2 ...
    primeira_adicao = tela.locator("#arvore-ast li:has(> .linha-no > .rotulo-no[data-tipo='ADICAO'])").first
    # A multiplicação está DENTRO (abaixo) da adição.
    expect(primeira_adicao.locator(".rotulo-no[data-tipo='MULTIPLICACAO']")).to_have_count(1)
    # 20 - 5 - 3: a subtração de dentro é (20 - 5).
    subtracao_externa = tela.locator("#arvore-ast li:has(> .linha-no > .rotulo-no[data-tipo='SUBTRACAO'])").first
    expect(subtracao_externa.locator(":scope > ul > li > .linha-no > .rotulo-no").first).to_have_attribute(
        "data-tipo", "SUBTRACAO")


def test_cada_no_mostra_forma_tipo_e_regra(tela):
    analisar(tela, "x = 1 + 2")
    adicao = no_ast(tela, "ADICAO")
    expect(adicao.locator(".forma")).to_have_text("◆")
    expect(adicao.locator(".tipo-no")).to_have_text("ADICAO")
    expect(adicao.locator(".regra-no")).to_have_text('soma = termo { ( "+" | "-" ) termo }')
    expect(no_ast(tela, "ATRIBUICAO").locator(".forma")).to_have_text("■")
    expect(no_ast(tela, "LITERAL_INTEIRO").first.locator(".forma")).to_have_text("●")


def test_comparacao_encadeada_e_chamada(tela):
    analisar(tela, "ok = 0 <= nota < 10\nprint(ok)")
    expect(no_ast(tela, "COMPARACAO")).to_contain_text("Comparação encadeada (<= <)")
    expect(no_ast(tela, "CHAMADA_FUNCAO")).to_contain_text("Chamada de função: print(…)")


def test_dez_niveis_de_parenteses_continuam_navegaveis(tela):  # CT-25
    analisar(tela, "x = " + "(" * 10 + "1 + 2" + ")" * 10)
    expect(tela.locator("#resultado-sintatico")).to_have_class("sucesso")
    expect(no_ast(tela, "ADICAO")).to_be_visible()  # os parênteses não viram nós
    tela.locator("#aba-derivacao").click()
    delimitadores = tela.locator("#arvore-derivacao .terminal[data-simbolo='DELIMITADOR']")
    expect(delimitadores).to_have_count(20)
    tela.locator("#recolher-tudo").click()
    expect(delimitadores.first).to_be_hidden()
    tela.locator("#expandir-tudo").click()
    expect(delimitadores.last).to_be_visible()


def test_so_comentario_gera_arvore_vazia(tela):  # CT-23
    analisar(tela, "# só um comentário")
    expect(tela.locator("#resultado-sintatico")).to_have_text(
        "Análise sintática concluída: 0 comando(s) reconhecido(s).")
    expect(tela.locator("#arvore-ast .rotulo-no")).to_have_count(1)  # só o Programa


# ---------- Seleção de nó ----------

def test_clicar_no_destaca_o_trecho_e_mostra_detalhes(tela):
    analisar(tela, "resultado = 10 + 5 * 2")
    no_ast(tela, "MULTIPLICACAO").click()
    expect(tela.locator("#codigo-colorido .no-selecionado")).to_have_text(["5", "*", "2"])
    expect(tela.locator("#detalhe-rotulo")).to_have_text("Multiplicação (*)")
    expect(tela.locator("#detalhe-regra")).to_have_text('termo = unario { ( "*" | "/" | "//" | "%" ) unario }')
    expect(tela.locator("#detalhe-posicao")).to_have_text("linha 1, coluna 18 até linha 1, coluna 22")
    expect(tela.locator("#detalhe-trecho")).to_have_text("5 * 2")

    no_ast(tela, "ADICAO").click()
    expect(tela.locator("#codigo-colorido .no-selecionado")).to_have_text(["10", "+", "5", "*", "2"])
    expect(tela.locator("#arvore-ast .rotulo-no.selecionado")).to_have_count(1)


def test_selecao_com_parenteses_e_varias_linhas(tela):
    analisar(tela, "total = (1 +\n         2) * 3")
    no_ast(tela, "MULTIPLICACAO").click()
    expect(tela.locator("#detalhe-trecho")).to_have_text("(1 +\n         2) * 3")


# ---------- Expandir e recolher ----------

def test_recolher_e_expandir_tudo(tela):
    analisar(tela, "x = 1 + 2 * 3")
    folhas = tela.locator("#arvore-ast .rotulo-no[data-tipo='LITERAL_INTEIRO']")
    expect(folhas.first).to_be_visible()
    tela.locator("#recolher-tudo").click()
    expect(folhas.first).to_be_hidden()
    expect(no_ast(tela, "PROGRAMA")).to_be_visible()     # a raiz continua aberta
    expect(no_ast(tela, "ATRIBUICAO")).to_be_visible()
    tela.locator("#expandir-tudo").click()
    expect(folhas).to_have_count(3)
    for i in range(3):
        expect(folhas.nth(i)).to_be_visible()


def test_recolher_um_no(tela):
    analisar(tela, "x = 1 + 2")
    item = tela.locator("#arvore-ast li:has(> .linha-no > .rotulo-no[data-tipo='ADICAO'])")
    alternar = item.locator(":scope > .linha-no > .alternar")
    alternar.click()
    expect(item).to_have_attribute("aria-expanded", "false")
    expect(item.locator(".rotulo-no[data-tipo='LITERAL_INTEIRO']").first).to_be_hidden()
    alternar.click()
    expect(item).to_have_attribute("aria-expanded", "true")


# ---------- Árvore de derivação ----------

def test_aba_de_derivacao(tela):
    analisar(tela, "x = (1)")
    expect(tela.locator("#painel-derivacao")).to_be_hidden()
    tela.locator("#aba-derivacao").click()
    expect(tela.locator("#painel-derivacao")).to_be_visible()
    expect(tela.locator("#painel-ast")).to_be_hidden()
    expect(tela.locator("#aba-derivacao")).to_have_attribute("aria-selected", "true")
    expect(tela.locator("#painel-derivacao .explicacao")).to_contain_text("árvore de derivação")
    nos_derivacao = tela.locator("#arvore-derivacao .rotulo-no").count()
    nos_ast = tela.locator("#arvore-ast .rotulo-no").count()
    assert nos_derivacao > nos_ast
    # Os parênteses aparecem na derivação, mas não na AST.
    expect(tela.locator("#arvore-derivacao .terminal[data-simbolo='DELIMITADOR']")).to_have_count(2)
    expect(tela.locator("#arvore-derivacao .nao-terminal[data-simbolo='atomo']").first).to_be_visible()


def test_contagem_compara_ast_e_derivacao(tela):
    analisar(tela, "x = 1")
    texto = tela.locator("#contagem-arvores").inner_text()
    assert texto.startswith("AST: 4 nós · Árvore de derivação: ")


def test_selecionar_nao_terminal_da_derivacao(tela):
    analisar(tela, "x = 10 + 5")
    tela.locator("#aba-derivacao").click()
    tela.locator("#arvore-derivacao .nao-terminal[data-simbolo='soma']").first.click()
    expect(tela.locator("#detalhe-rotulo")).to_have_text("Não terminal: soma")
    expect(tela.locator("#detalhe-regra")).to_have_text('soma = termo { ( "+" | "-" ) termo }')
    expect(tela.locator("#codigo-colorido .no-selecionado")).to_have_text(["10", "+", "5"])


def test_folhas_da_derivacao_sao_os_tokens_da_tabela(tela):  # 7.3.1 consistência
    analisar(tela, 'print("Oi", 1 + 2)')
    tela.locator("#aba-derivacao").click()
    folhas = tela.locator("#arvore-derivacao .terminal .tipo-no").all_inner_texts()
    tipos_tabela = [linha.locator("td").nth(1).inner_text()
                    for linha in tela.locator("#tabela-tokens tbody tr").all()]
    assert folhas == tipos_tabela


# ---------- Passo a passo da construção ----------

def test_construcao_passo_a_passo(tela):
    analisar(tela, "r = 10 + 5 * 2")  # 8 nós
    explicacao = tela.locator("#arvore-explicacao")
    expect(explicacao).to_contain_text("A AST tem 8 nó(s)")
    expect(tela.locator("#arvore-anterior")).to_be_disabled()

    tela.locator("#arvore-proximo").click()
    expect(tela.locator("#arvore-ast .no-atual")).to_have_attribute("data-tipo", "IDENTIFICADOR")
    expect(tela.locator("#arvore-ast .pendente")).to_have_count(7)
    expect(explicacao).to_contain_text("Passo 1 de 8: o parser reconheceu Identificador: r")

    for _ in range(4):
        tela.locator("#arvore-proximo").click()
    # Passo 5: a multiplicação nasce antes da adição (filhos antes do pai).
    expect(tela.locator("#arvore-ast .no-atual")).to_have_attribute("data-tipo", "MULTIPLICACAO")
    expect(explicacao).to_contain_text('Passo 5 de 8: o parser reconheceu Multiplicação (*) pela regra termo')
    expect(explicacao).to_contain_text('a partir do trecho "5 * 2"')
    expect(tela.locator("#codigo-colorido .no-selecionado")).to_have_text(["5", "*", "2"])
    expect(no_ast(tela, "ADICAO")).to_have_class(re.compile(r"\bpendente\b"))

    tela.locator("#arvore-anterior").click()
    expect(tela.locator("#arvore-ast .no-atual")).to_have_attribute("data-tipo", "LITERAL_INTEIRO")


def test_construcao_termina_no_programa(tela):
    analisar(tela, "x = 1")
    for _ in range(4):
        tela.locator("#arvore-proximo").click()
    expect(tela.locator("#arvore-ast .no-atual")).to_have_attribute("data-tipo", "PROGRAMA")
    expect(tela.locator("#arvore-ast .pendente")).to_have_count(0)
    expect(tela.locator("#arvore-proximo")).to_be_disabled()


def test_reproduzir_construcao(tela):
    analisar(tela, "x = 1")
    tela.locator("#arvore-reproduzir").click()
    expect(tela.locator("#arvore-reproduzir")).to_have_text("⏸ Pausar")
    expect(tela.locator("#arvore-explicacao")).to_contain_text("Passo 4 de 4", timeout=8000)
    expect(tela.locator("#arvore-reproduzir")).to_have_text("▶ Reproduzir")


def test_passo_a_passo_abre_nos_recolhidos(tela):
    analisar(tela, "x = 1 + 2")
    tela.locator("#recolher-tudo").click()
    tela.locator("#arvore-proximo").click()
    tela.locator("#arvore-proximo").click()  # passo 2: o literal 1, dentro da adição recolhida
    expect(tela.locator("#arvore-ast .no-atual")).to_be_visible()


# ---------- Erros sintáticos ----------

def test_erros_sintaticos_do_exemplo_10(tela):
    analisar(tela, exemplo="9")
    expect(tela.locator("#resultado")).to_have_class("sucesso")  # o léxico passou
    expect(tela.locator("#resultado-sintatico")).to_have_text(
        "A análise sintática encontrou 4 erro(s). Veja os detalhes abaixo.")
    erros = tela.locator("#lista-erros-sintaticos li")
    expect(erros).to_have_count(4)
    expect(erros.nth(0)).to_contain_text("Erro sintático na linha 1, coluna 8: expressão incompleta")
    expect(erros.nth(0)).to_contain_text("Encontrado: o fim da linha")
    expect(erros.nth(0)).to_contain_text("Regra da gramática:")
    expect(erros.nth(2)).to_contain_text("este ')' está sobrando")
    expect(erros.nth(3)).to_contain_text("só um nome (identificador) pode receber um valor")
    expect(tela.locator("#secao-arvore")).to_be_hidden()  # sem AST quando há erro sintático


def test_erro_mostra_esperado_e_encontrado(tela):
    analisar(tela, 'print("a" "b")')
    erro = tela.locator("#lista-erros-sintaticos li")
    expect(erro).to_contain_text('Encontrado: \'"b"\' · Esperado: ,, )')
    expect(erro.locator("code")).to_have_text('argumentos = expressao { "," expressao }')


def test_erro_sintatico_sublinhado_no_codigo(tela):
    analisar(tela, "x = 1 + * 2")
    expect(tela.locator("#codigo-colorido .tk-erro-sintatico")).to_have_text("*")


def test_erro_no_fim_do_codigo_ganha_marca(tela):  # CT-16
    analisar(tela, "print(")
    expect(tela.locator("#codigo-colorido .marca-erro-sintatico")).to_have_count(1)
    expect(tela.locator("#lista-erros-sintaticos li")).to_contain_text("o código terminou antes de fechar")


def test_erro_lexico_e_sintatico_tem_rotulos_diferentes(tela):
    analisar(tela, "a = 1 $\nb = (2")
    expect(tela.locator("#secao-erros h3")).to_contain_text("Léxico")
    expect(tela.locator("#secao-erros-sintaticos h3")).to_contain_text("Sintático")
    expect(tela.locator("#lista-erros li")).to_have_count(1)
    expect(tela.locator("#lista-erros-sintaticos li")).to_have_count(1)
    expect(tela.locator("#lista-erros li")).to_contain_text("Erro léxico")
    expect(tela.locator("#lista-erros-sintaticos li")).to_contain_text("Erro sintático")


def test_linha_com_erro_lexico_e_pulada_e_o_resto_vira_arvore(tela):  # CT-27
    analisar(tela, "x = 1 @ 2\ny = 2 + 3")
    expect(tela.locator("#resultado")).to_have_class("aviso")
    expect(tela.locator("#resultado-sintatico")).to_have_text(
        "Análise sintática concluída: 1 comando(s) reconhecido(s). "
        "Linha(s) não analisada(s) por ter(em) erro léxico: 1.")
    expect(tela.locator("#resultado-sintatico")).to_have_class("aviso")
    expect(tela.locator("#secao-erros-sintaticos")).to_be_hidden()
    expect(no_ast(tela, "ATRIBUICAO")).to_contain_text("Atribuição: y = …")


def test_correcao_faz_os_erros_sumirem(tela):
    analisar(tela, "x = 5 +")
    expect(tela.locator("#secao-erros-sintaticos")).to_be_visible()
    analisar(tela, "x = 5 + 1")
    expect(tela.locator("#secao-erros-sintaticos")).to_be_hidden()
    expect(tela.locator("#secao-arvore")).to_be_visible()


# ---------- Robustez ----------

@pytest.mark.parametrize("codigo", [
    "x = " + "(" * 200 + "1" + ")" * 200,
    "= = = = =",
    ")))(((",
    "x = 1 2 3 4 5\n" * 50,
    "f(1)(2)(3)(4)(5)",
    "x = " + " + ".join(["1"] * 200),
])
def test_entradas_invalidas_ou_grandes_nao_quebram(tela, codigo):
    erros_js = []
    tela.on("pageerror", lambda erro: erros_js.append(erro))
    analisar(tela, codigo)
    expect(tela.locator("#resultado-sintatico")).to_be_visible()
    expect(tela.locator("#analisar")).to_be_enabled()
    assert erros_js == []
    analisar(tela, "x = 1")
    expect(tela.locator("#resultado-sintatico")).to_have_class("sucesso")


def test_codigo_com_html_na_arvore_aparece_como_texto(tela):
    analisar(tela, 'x = "<img src=x onerror=alert(1)>"')
    expect(tela.locator("#arvore-ast img")).to_have_count(0)
    expect(no_ast(tela, "LITERAL_STRING")).to_contain_text('String: "<img src=x onerror=alert(1)>"')


def test_falha_de_comunicacao_esconde_a_arvore_anterior(tela):
    analisar(tela, "x = 1")
    expect(tela.locator("#secao-arvore")).to_be_visible()
    tela.route("**/api/analisar", lambda rota: rota.abort())
    tela.locator("#codigo").fill("y = 2")
    tela.locator("#analisar").click()
    expect(tela.locator("#resultado")).to_have_class("erro")
    expect(tela.locator("#resultado-sintatico")).to_be_hidden()
    expect(tela.locator("#secao-arvore")).to_be_hidden()


def test_explicacao_de_analise_sintatica(tela):
    tela.locator("#o-que-e-sintatica summary").click()
    expect(tela.locator("#o-que-e-sintatica")).to_contain_text("árvore de derivação")
    expect(tela.locator("#o-que-e-sintatica")).to_contain_text("AST")


# ---------- Celular ----------

def test_celular_sem_rolagem_horizontal_com_arvore(tela):
    tela.set_viewport_size({"width": 375, "height": 740})
    analisar(tela, exemplo="8")
    tela.locator("#aba-derivacao").click()
    largura = tela.evaluate("document.documentElement.scrollWidth")
    assert largura <= 375


# ---------- Evidências (prints) ----------

def salvar_print(tela, nome):
    os.makedirs(PASTA_EVIDENCIAS, exist_ok=True)
    tela.screenshot(path=os.path.join(PASTA_EVIDENCIAS, nome), full_page=True)


def test_gera_print_da_arvore(tela):
    tela.set_viewport_size({"width": 1000, "height": 800})
    analisar(tela, "resultado = 10 + 5 * 2")
    for _ in range(5):  # para na multiplicação, para mostrar a construção passo a passo
        tela.locator("#arvore-proximo").click()
    expect(tela.locator("#arvore-ast .no-atual")).to_have_attribute("data-tipo", "MULTIPLICACAO")
    tela.locator("#secao-arvore").scroll_into_view_if_needed()
    salvar_print(tela, "arvore-sintatica.png")


def test_gera_print_da_selecao_e_derivacao(tela):
    tela.set_viewport_size({"width": 1000, "height": 800})
    analisar(tela, "resultado = 10 + 5 * 2")
    tela.locator("#aba-derivacao").click()
    tela.locator("#arvore-derivacao .nao-terminal[data-simbolo='termo']").nth(1).click()
    salvar_print(tela, "arvore-derivacao.png")


def test_gera_print_dos_erros_sintaticos(tela):
    tela.set_viewport_size({"width": 1000, "height": 800})
    analisar(tela, exemplo="9")
    salvar_print(tela, "erros-sintaticos.png")


def test_gera_print_da_arvore_no_celular(tela):
    tela.set_viewport_size({"width": 375, "height": 740})
    analisar(tela, exemplo="7")
    salvar_print(tela, "celular-arvore.png")
