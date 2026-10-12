# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
r"""Testes: mapa de pseudonimos com tokens estaveis.

Valida que a mesma chave normalizada sempre retorna o mesmo token,
que valores novos ganham numeros sequenciais, e que a gravacao e'
atomica (nao deixa mapa corrupto no disco).

Rodar: python -X utf8 testes/test_mapa_pseudonimos.py
"""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pseudonimizador.motor.mapa import (NOME_ARQUIVO_MAPA, carregar_mapa,
                                              gravar_mapa, normalizar, token_para)

def test_normalizar_tira_acento_caixa_e_espacos():
    assert normalizar("  João   da SILVA ") == "joao da silva"

def test_token_estavel_para_o_mesmo_valor():
    m = carregar_mapa(Path(tempfile.gettempdir()) / "nao-existe", "0000000-00")
    t1 = token_para(m, "RECLAMANTE", "pessoa", "João da Silva", papel="Reclamante")
    t2 = token_para(m, "RECLAMANTE", "pessoa", "JOAO DA SILVA")  # variante de OCR
    assert t1 == "[[RECLAMANTE_1]]" and t2 == t1
    assert m["tokens"][t1]["valor"] == "João da Silva"
    assert m["tokens"][t1]["papel"] == "Reclamante"
    assert m["tokens"][t1]["variantes_vistas"] == []

def test_valor_novo_ganha_o_proximo_numero_sem_realocar():
    m = carregar_mapa(Path(tempfile.gettempdir()) / "nao-existe", "0000000-00")
    token_para(m, "CPF", "cpf", "111.111.111-11")
    t2 = token_para(m, "CPF", "cpf", "222.222.222-22")
    assert t2 == "[[CPF_2]]"
    assert token_para(m, "CPF", "cpf", "111.111.111-11") == "[[CPF_1]]"

def test_gravacao_atomica_e_recarga():
    with tempfile.TemporaryDirectory() as td:
        pasta = Path(td) / "0020000-00.2026.5.04.9999"
        m = carregar_mapa(pasta, "0020000-00.2026.5.04.9999")
        token_para(m, "RECLAMANTE", "pessoa", "Maria Souza")
        caminho = gravar_mapa(pasta, m)
        assert caminho.name == NOME_ARQUIVO_MAPA and caminho.is_file()
        assert not list(pasta.glob("*.tmp"))
        m2 = carregar_mapa(pasta, "0020000-00.2026.5.04.9999")
        assert token_para(m2, "RECLAMANTE", "pessoa", "Maria Souza") == "[[RECLAMANTE_1]]"

if __name__ == "__main__":
    testes = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("test_") and callable(f)]
    falhas = 0
    for nome, fn in testes:
        try:
            fn()
            print(f"ok    {nome}")
        except AssertionError as e:
            falhas += 1
            print(f"FALHA {nome}\n      {e}")
        except Exception as e:  # noqa: BLE001
            falhas += 1
            print(f"FALHA {nome}\n      {e!r}")
    print(f"\n{len(testes) - falhas}/{len(testes)} passaram, {falhas} falha(s)")
    sys.exit(1 if falhas else 0)
