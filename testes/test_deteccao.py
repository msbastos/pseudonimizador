# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
import _base  # noqa: F401
import fabrica as F
from pseudonimizador.deteccao import detectar

TEXTO = "\n".join(F.LINHAS_CONTRATO)


def _por_categoria(texto):
    achados = {}
    for o in detectar(texto):
        achados.setdefault(o.categoria, set()).add(o.valor)
    return achados


def test_contrato_completo():
    a = _por_categoria(TEXTO)
    assert F.PESSOA_1 in a["pessoa"] and F.PESSOA_2 in a["pessoa"], a
    assert F.EMPRESA in a["empresa"], a
    assert F.CPF in a["cpf"] and F.CNPJ in a["cnpj"], a
    assert F.EMAIL in a["email"], a
    assert any(F.TELEFONE in v for v in a["telefone"]), a
    assert any("Acácias" in v for v in a["endereco"]), a


def test_sem_falso_positivo_nas_clausulas():
    a = _por_categoria("Cláusula 1ª. O aluguel mensal é de R$ 1.500,00.\nPorto Alegre, 11 de outubro de 2026.")
    assert not a.get("pessoa") and not a.get("empresa"), a


def test_nome_fora_do_lexico_pela_ancora_e_pela_qualificacao():
    a = _por_categoria("CONTRATANTE: Xandrelo Quintebor Vasques, brasileiro, solteiro.\n"
                       "e Ylmara Torquesi Bento, portadora do RG 1234567.")
    assert "Xandrelo Quintebor Vasques" in a["pessoa"], a
    assert "Ylmara Torquesi Bento" in a["pessoa"], a


def test_caixa_nao_decide():
    a = _por_categoria("assinado por maria aparecida pereira em 2026.")
    assert "maria aparecida pereira" in a["pessoa"], a


def test_ocorrencias_ordenadas_sem_sobreposicao():
    oc = detectar(TEXTO)
    for x, y in zip(oc, oc[1:]):
        assert x.fim <= y.ini, (x, y)
    assert all(TEXTO[o.ini:o.fim] == o.valor for o in oc)


def test_endereco_com_nome_de_pessoa_na_rua_fica_inteiro():
    a = _por_categoria("residente na Rua Joaquim Nabuco, 123, apto 45, CEP 90000-000.")
    assert any("Joaquim Nabuco" in v and "123" in v for v in a.get("endereco", ())), a
    assert "Joaquim Nabuco" not in a.get("pessoa", ()), a
    a = _por_categoria("Avenida Getúlio Vargas, 1500")
    assert any("Getúlio Vargas" in v and "1500" in v for v in a.get("endereco", ())), a
    assert "Getúlio Vargas" not in a.get("pessoa", ()), a


def test_pronome_me_nao_vira_sufixo_de_empresa():
    a = _por_categoria("Ficou acertado que Maria Pereira me pagará o valor.")
    assert "Maria Pereira" in a["pessoa"] and not a.get("empresa"), a
    a = _por_categoria("Padaria Bom Pão ME, CNPJ 11.222.333/0001-81")
    assert "Padaria Bom Pão ME" in a["empresa"], a


def test_duas_pessoas_ligadas_por_e_sao_dois_nomes():
    a = _por_categoria("Assinaram João Silva e Maria Souza o presente.")
    assert {"João Silva", "Maria Souza"} <= a["pessoa"], a


def test_inicial_do_meio_nao_corta_o_nome():
    a = _por_categoria("CONTRATANTE: Maria da S. Pereira, brasileira.")
    assert "Maria da S. Pereira" in a["pessoa"], a
    a = _por_categoria("assinado por João C. Souza.")
    assert "João C. Souza" in a["pessoa"], a


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
