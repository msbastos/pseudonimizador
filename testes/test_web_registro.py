# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Registro em memória dos documentos e a fila única de trabalho."""
import _base  # noqa: F401
import threading
import time

import fabrica as F
from pseudonimizador.estado import abrir_log
from pseudonimizador.leitura import ler
from pseudonimizador.web.registro import Fila, Registro


def _esperar(condicao, prazo=60.0):
    fim = time.monotonic() + prazo
    while not condicao():
        assert time.monotonic() < fim, "esperou demais"
        time.sleep(0.05)


def test_fila_um_trabalho_de_cada_vez_e_encerrar_descarta_os_pendentes():
    pasta = F.pasta_temporaria("registro_fila")
    fila = Fila(abrir_log(pasta))
    marcas = []

    def trabalho(n):
        def f():
            marcas.append(f"ini{n}")
            time.sleep(0.2)
            marcas.append(f"fim{n}")
        return f
    fila.enfileirar(trabalho(1))
    fila.enfileirar(trabalho(2))
    assert fila.ocupada()
    _esperar(lambda: len(marcas) == 4)
    assert marcas == ["ini1", "fim1", "ini2", "fim2"]
    _esperar(lambda: not fila.ocupada(), prazo=5)
    marcas.clear()
    fila.enfileirar(trabalho(3))
    fila.enfileirar(trabalho(4))
    _esperar(lambda: "ini3" in marcas)
    assert fila.encerrar(timeout=5)
    assert marcas == ["ini3", "fim3"] and not fila.ocupada()


def test_registrar_upload_ler_decidir_acrescentar_gerar():
    pasta = F.pasta_temporaria("registro_fluxo")
    reg = Registro(pasta / "tmp", abrir_log(pasta))
    original = F.contrato_docx(pasta / "contrato.docx").read_bytes()
    doc = reg.registrar_upload("contrato.docx", [original[:100], original[100:]])
    assert doc.situacao == "lendo" and doc.origem == "janela" and (pasta / "tmp" / doc.id / "contrato.docx").is_file()
    _esperar(lambda: doc.situacao != "lendo")
    assert doc.situacao == "revisao", doc.erro
    d = reg.detalhe(doc.id)
    assert d["revisavel"] and {it["valor"] for it in d["itens"]} >= {F.PESSOA_1, F.CPF, F.EMAIL}
    item = next(it for it in d["itens"] if it["valor"] == F.EMAIL)
    assert item["aceito"] and item["ocorrencias"] >= 1 and 1 <= len(item["contextos"]) <= 3
    reg.decidir(doc.id, "email", F.EMAIL, False)
    assert not next(it for it in reg.detalhe(doc.id)["itens"] if it["valor"] == F.EMAIL)["aceito"]
    extra = reg.acrescentar(doc.id, "Porto Alegre", "outro")
    assert extra["acrescido"] and extra["ocorrencias"] == 1
    try:
        reg.acrescentar(doc.id, "texto que não está no documento", "outro")
    except ValueError:
        pass
    else:
        raise AssertionError("acrescentar o que não existe deveria falhar")
    try:
        reg.decidir(doc.id, "pessoa", "Ninguém Assim", True)
    except LookupError:
        pass
    else:
        raise AssertionError("decisão sobre item inexistente deveria falhar")
    reg.pedir_geracao(doc.id, formato="layout", tipo=None, modo="reversivel",
                      pasta_saida=pasta / "Saida", pasta_mapas=pasta / "Mapas")
    assert doc.situacao == "gerando"
    _esperar(lambda: doc.situacao != "gerando")
    assert doc.situacao == "pronto", doc.erro
    r = reg.detalhe(doc.id)["resultado"]
    assert r["saida_nome"] == "contrato - pseudonimizado.docx" and r["mapa_nome"].endswith(".json")
    texto = ler(pasta / "Saida" / r["saida_nome"]).texto
    assert F.EMAIL in texto and "Porto Alegre" not in texto and F.PESSOA_1 not in texto
    assert not (pasta / "tmp" / doc.id).exists()        # o tmp vai embora depois de gerar
    assert [x["id"] for x in reg.lista()] == [doc.id]
    reg.descartar(doc.id)
    assert reg.lista() == []
    assert reg.encerrar(timeout=5)


def test_erro_de_leitura_vira_situacao_erro_sem_revisao():
    pasta = F.pasta_temporaria("registro_erro")
    reg = Registro(pasta / "tmp", abrir_log(pasta))
    doc = reg.registrar_upload("x.docx", [b"isto nao e um docx"])
    _esperar(lambda: doc.situacao != "lendo")
    assert doc.situacao == "erro" and doc.erro["mensagem"] and doc.erro["valores"] == []
    assert not reg.detalhe(doc.id)["revisavel"] and reg.detalhe(doc.id)["itens"] == []
    for nome in ("notas.txt", "", "..", "sub\\..\\x.exe"):
        try:
            reg.registrar_upload(nome, [b"a"])
        except ValueError:
            pass
        else:
            raise AssertionError(f"deveria recusar {nome!r}")
    try:
        reg.pedir_geracao(doc.id, formato="layout", tipo=None, modo="definitivo",
                          pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    except RuntimeError:
        pass
    else:
        raise AssertionError("gerar sem revisão deveria falhar")
    assert reg.encerrar(timeout=5)


def test_descartar_durante_a_leitura_apaga_o_tmp_depois():
    pasta = F.pasta_temporaria("registro_descartar")
    comecou = threading.Event()

    def ler_lento(caminho):
        comecou.set()
        time.sleep(0.5)
        return ler(caminho)
    reg = Registro(pasta / "tmp", abrir_log(pasta), ler=ler_lento)
    doc = reg.registrar_upload("contrato.docx", [F.contrato_docx(pasta / "c.docx").read_bytes()])
    assert comecou.wait(10)
    reg.descartar(doc.id)
    assert reg.lista() == []
    _esperar(lambda: not reg.fila.ocupada())
    _esperar(lambda: not (pasta / "tmp" / doc.id).exists(), prazo=5)
    assert reg.encerrar(timeout=5)


def test_encerrar_espera_a_leitura_em_curso():
    """Fechar no meio do OCR: o trabalho em curso termina (nunca é morto),
    os pendentes são descartados e o tmp some."""
    pasta = F.pasta_temporaria("registro_encerrar")
    marcas = []

    def ler_lento(caminho):
        marcas.append("ini")
        time.sleep(0.5)
        marcas.append("fim")
        return ler(caminho)
    reg = Registro(pasta / "tmp", abrir_log(pasta), ler=ler_lento)
    corpo = F.contrato_docx(pasta / "c.docx").read_bytes()
    a = reg.registrar_upload("a.docx", [corpo])
    b = reg.registrar_upload("b.docx", [corpo])
    _esperar(lambda: "ini" in marcas)
    assert reg.encerrar(timeout=10)
    assert marcas == ["ini", "fim"] and a.situacao == "revisao" and b.situacao == "lendo"
    assert not (pasta / "tmp" / a.id).exists() and not (pasta / "tmp" / b.id).exists()


def test_ocr_serializado_pela_trava():
    import fitz
    from pseudonimizador.leitura import ocr
    assert isinstance(ocr._TRAVA, type(threading.Lock()))

    class MotorFalso:
        def __call__(self, imagem):
            assert ocr._TRAVA.locked(), "o OCR rodou fora da trava"
            return None
    original = ocr._motor
    ocr._motor = lambda: MotorFalso()
    try:
        doc = fitz.open()
        pagina = doc.new_page(width=50, height=50)
        pix = pagina.get_pixmap(colorspace=fitz.csRGB, alpha=False)
        assert ocr.ocr_pixmap(pix) == []
        assert ocr.ocr_pagina(pagina) == []
    finally:
        ocr._motor = original


def test_descartado_cuja_leitura_falha_nao_deixa_tmp():
    pasta = F.pasta_temporaria("registro_descartado_falha")
    comecou, solta = threading.Event(), threading.Event()

    def ler_que_falha(caminho):
        comecou.set()
        solta.wait(10)
        raise OSError("arquivo preso")
    reg = Registro(pasta / "tmp", abrir_log(pasta), ler=ler_que_falha)
    doc = reg.registrar_upload("c.docx", [F.contrato_docx(pasta / "c.docx").read_bytes()])
    assert comecou.wait(10)
    reg.descartar(doc.id)
    solta.set()
    _esperar(lambda: not reg.fila.ocupada())
    assert not (pasta / "tmp" / doc.id).exists()
    assert reg.encerrar(timeout=5)


def test_tmp_de_execucao_anterior_e_limpo_na_criacao():
    pasta = F.pasta_temporaria("registro_tmp_velho")
    velho = pasta / "tmp" / "abc123"
    velho.mkdir(parents=True)
    (velho / "x.docx").write_bytes(b"resto")
    reg = Registro(pasta / "tmp", abrir_log(pasta))
    assert not velho.exists()
    assert reg.encerrar(timeout=5)


def test_geracao_duas_vezes_recusa_a_segunda_e_nao_edita_gerando():
    pasta = F.pasta_temporaria("registro_gerar_duas")
    chamadas, solta = [], threading.Event()

    def gerar_lento(*a, **k):
        chamadas.append(1)
        solta.wait(10)
        raise ValueError("recusado de propósito")
    reg = Registro(pasta / "tmp", abrir_log(pasta), gerar=gerar_lento)
    doc = reg.registrar_upload("c.docx", [F.contrato_docx(pasta / "c.docx").read_bytes()])
    _esperar(lambda: doc.situacao == "revisao")
    args = dict(formato="layout", tipo=None, modo="reversivel", pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    reg.pedir_geracao(doc.id, **args)
    for chamada in (lambda: reg.pedir_geracao(doc.id, **args),
                    lambda: reg.decidir(doc.id, "email", F.EMAIL, False),
                    lambda: reg.acrescentar(doc.id, "Porto Alegre", "outro")):
        try:
            chamada()
        except (ValueError, RuntimeError):
            pass
        else:
            raise AssertionError("deveria recusar enquanto gera")
    solta.set()
    _esperar(lambda: doc.situacao == "erro")
    assert len(chamadas) == 1
    assert reg.encerrar(timeout=5)


def test_descartado_durante_a_geracao_nao_deixa_saida_nem_chama_apos_gerar():
    pasta = F.pasta_temporaria("registro_gerar_descartado")
    solta, apos = threading.Event(), []
    from pseudonimizador.saida import gerar as gerar_real

    def gerar_lento(*a, **k):
        solta.wait(10)
        return gerar_real(*a, **k)
    reg = Registro(pasta / "tmp", abrir_log(pasta), gerar=gerar_lento, apos_gerar=apos.append)
    doc = reg.registrar_upload("c.docx", [F.contrato_docx(pasta / "c.docx").read_bytes()])
    _esperar(lambda: doc.situacao == "revisao")
    reg.pedir_geracao(doc.id, formato="layout", tipo=None, modo="reversivel",
                      pasta_saida=pasta / "S", pasta_mapas=pasta / "M")
    reg.descartar(doc.id)
    solta.set()
    _esperar(lambda: not reg.fila.ocupada())
    assert apos == []
    assert not list((pasta / "S").glob("*")) and not list((pasta / "M").glob("*"))
    assert reg.encerrar(timeout=5)


def test_upload_invalido_ou_depois_de_encerrar():
    pasta = F.pasta_temporaria("registro_upload_invalido")
    reg = Registro(pasta / "tmp", abrir_log(pasta))
    for nome in ("x.docx:y.pdf", "a<b.pdf", 'a"b.pdf', "a|b.pdf", "a?b.pdf", "a*b.pdf", "ab.pdf"):
        try:
            reg.registrar_upload(nome, [b"a"])
        except ValueError:
            pass
        else:
            raise AssertionError(f"deveria recusar {nome!r}")
    assert reg.encerrar(timeout=5)
    try:
        reg.registrar_upload("ok.docx", [b"a"])
    except RuntimeError:
        pass
    else:
        raise AssertionError("depois de encerrar deveria recusar")
    assert list((pasta / "tmp").iterdir()) == []


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
