# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""O motor copiado não depende de nada do Ulpiano e troca tudo, sempre."""
import _base  # noqa: F401
import re
from _base import RAIZ


def test_nenhum_import_fora_do_motor():
    for arq in (RAIZ / "pseudonimizador" / "motor").glob("*.py"):
        texto = arq.read_text(encoding="utf-8")
        assert not re.search(r"^\s*from\s+\.\.", texto, re.M), f"{arq.name} importa de fora do motor"
        assert not re.search(r"^\s*(from|import)\s+ulpiano\b", texto, re.M), f"{arq.name} importa o Ulpiano"


def test_nomes_e_empresas_sempre_em_codigo():
    from pseudonimizador.motor import mapa as M
    from pseudonimizador.motor.pseudonimizador import pseudonimizar
    mapa = M.novo_mapa()
    M.token_para(mapa, "PESSOA", "pessoa", "Maria Aparecida Pereira")
    M.token_para(mapa, "EMPRESA", "pj", "Exemplo Comércio de Tecidos Ltda.")
    saida = pseudonimizar("Maria Aparecida Pereira assina por Exemplo Comércio de Tecidos Ltda.", mapa)
    assert "Maria" not in saida and "Exemplo" not in saida, saida
    assert "[[PESSOA_1]]" in saida and "[[EMPRESA_1]]" in saida, saida


def test_escrever_atomico(tmp=RAIZ / "saida_testes" / "atomico.json"):
    from pseudonimizador.motor.mapa import escrever_atomico
    escrever_atomico(tmp, '{"a": 1}')
    assert tmp.read_text(encoding="utf-8") == '{"a": 1}'
    assert not tmp.with_suffix(".json.tmp").exists()


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
