# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Pasta monitorada: arquivo estável vira Pendente; ocultos, ~$ e Processados
ignorados; depois de gerar o original vai para Processados; erro não reprocessa."""
import _base  # noqa: F401
import os
import time

import fabrica as F
from _web import ServidorDeTeste
from pseudonimizador.estado import abrir_log
from pseudonimizador.web.pasta_monitorada import Vigia
from pseudonimizador.web.registro import Registro


def _esperar(condicao, prazo=60.0):
    fim = time.monotonic() + prazo
    while not condicao():
        assert time.monotonic() < fim, "esperou demais"
        time.sleep(0.05)


def _vigia(nome):
    pasta = F.pasta_temporaria(nome)
    log = abrir_log(pasta)
    reg = Registro(pasta / "tmp", log)
    entrada = pasta / "Entrada"
    entrada.mkdir()
    v = Vigia(reg, entrada, entrada / "Processados", log, intervalo_s=0.05)
    reg.apos_gerar = v.processado
    return pasta, reg, entrada, v


def test_arquivo_so_entra_quando_estavel():
    """Review Focus 3: arquivo ainda sendo copiado para a Entrada."""
    pasta, reg, entrada, v = _vigia("pasta_estavel")
    corpo = F.contrato_docx(pasta / "c.docx").read_bytes()
    alvo = entrada / "contrato.docx"
    with open(alvo, "wb") as f:
        f.write(corpo[:200])
        f.flush()
        assert v.varrer() == []                 # primeira vez: só anota
        f.write(corpo[200:])
        f.flush()
        os.utime(alvo, None)
    assert v.varrer() == []                     # mudou desde a última varredura
    novos = v.varrer()                          # igual em duas seguidas: entra
    assert len(novos) == 1 and novos[0].origem == "pasta" and novos[0].nome == "contrato.docx"
    assert v.varrer() == []                     # não entra duas vezes
    _esperar(lambda: novos[0].situacao != "lendo")
    assert novos[0].situacao == "revisao" and reg.lista()[0]["origem"] == "pasta"
    assert reg.encerrar(timeout=5)


def test_ignora_ocultos_temporarios_vazios_e_processados():
    pasta, reg, entrada, v = _vigia("pasta_ignora")
    corpo = F.contrato_docx(pasta / "c.docx").read_bytes()
    (entrada / "~$contrato.docx").write_bytes(corpo)
    (entrada / ".escondido.docx").write_bytes(corpo)
    (entrada / "notas.txt").write_bytes(b"x")
    (entrada / "vazio.pdf").write_bytes(b"")
    (entrada / "Processados").mkdir()
    (entrada / "Processados" / "antigo.docx").write_bytes(corpo)
    (entrada / "outra_pasta").mkdir()
    oculto = entrada / "atributo.docx"
    oculto.write_bytes(corpo)
    os.system(f'attrib +h "{oculto}"')
    assert v.varrer() == [] and v.varrer() == []
    assert reg.lista() == []
    assert reg.encerrar(timeout=5)


def test_depois_de_gerar_o_original_vai_para_processados():
    with ServidorDeTeste("pasta_gerar", vigia_pasta_s=0.05) as s:
        entrada = s.pasta / "Base" / "Entrada"
        F.contrato_docx(entrada / "lote.docx")
        F.contrato_docx(entrada / "Processados" / "lote.docx")      # colisão: o novo ganha " (2)"
        _esperar(lambda: s.get("/api/documentos")[1]["documentos"] != [])
        d = s.get("/api/documentos")[1]["documentos"][0]
        assert d["origem"] == "pasta" and d["nome"] == "lote.docx"
        s.esperar(d["id"], "revisao")
        assert s.post(f"/api/documentos/{d['id']}/gerar", {})[0] == 202
        r = s.esperar(d["id"], "pronto", "erro")
        assert r["situacao"] == "pronto", r["erro"]
        assert (s.pasta / "Base" / "Saida" / "lote - pseudonimizado.docx").is_file()
        assert not (entrada / "lote.docx").exists()
        assert (entrada / "Processados" / "lote (2).docx").is_file()
        # posto de novo na Entrada (é outro arquivo): entra de novo
        F.contrato_docx(entrada / "lote.docx")
        _esperar(lambda: len(s.get("/api/documentos")[1]["documentos"]) == 2)
    log = s.log_texto()
    assert "pasta monitorada" in log and "lote" not in log


def test_erro_de_leitura_fica_na_entrada_sem_reprocessar():
    pasta, reg, entrada, v = _vigia("pasta_erro")
    ruim = entrada / "ruim.docx"
    ruim.write_bytes(b"nao e docx")
    assert v.varrer() == []
    novos = v.varrer()
    assert len(novos) == 1
    _esperar(lambda: novos[0].situacao != "lendo")
    assert novos[0].situacao == "erro" and ruim.exists()
    assert v.varrer() == [] and v.varrer() == []            # não reprocessa até mudar
    ruim.write_bytes(F.contrato_docx(pasta / "c.docx").read_bytes())
    os.utime(ruim, (time.time() + 5, time.time() + 5))
    assert v.varrer() == []
    assert len(v.varrer()) == 1                              # mudou: entra de novo
    assert reg.encerrar(timeout=5)


def test_trocar_de_pasta_e_parar():
    pasta, reg, entrada, v = _vigia("pasta_trocar")
    nova = pasta / "Entrada2"
    nova.mkdir()
    F.contrato_docx(nova / "x.docx")
    v.trocar(nova, nova / "Processados")
    v.iniciar()
    _esperar(lambda: reg.lista() != [], prazo=10)
    assert reg.lista()[0]["nome"] == "x.docx"
    v.parar()
    assert reg.encerrar(timeout=5)


def test_descartado_nao_move_e_arquivo_preso_tenta_de_novo():
    from pseudonimizador.web import pasta_monitorada as pm
    pasta, reg, entrada, v = _vigia("pasta_preso")
    F.contrato_docx(entrada / "a.docx")
    F.contrato_docx(entrada / "b.docx")
    v.varrer()
    a, b = sorted(v.varrer(), key=lambda d: d.nome)
    _esperar(lambda: a.situacao != "lendo" and b.situacao != "lendo")
    a.descartado = True
    v.processado(a)
    assert (entrada / "a.docx").exists()                     # descartado: o original fica
    original = pm.shutil.move
    chamadas = []

    def preso(*args, **kw):
        chamadas.append(1)
        if len(chamadas) == 1:
            raise PermissionError("preso")
        return original(*args, **kw)
    pm.shutil.move = preso
    try:
        v.processado(b)
        assert (entrada / "b.docx").exists()                 # preso: fica
        v.varrer()                                           # a próxima varredura tenta de novo
        assert not (entrada / "b.docx").exists()
        assert (entrada / "Processados" / "b.docx").is_file()
    finally:
        pm.shutil.move = original
    assert reg.encerrar(timeout=5)


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
