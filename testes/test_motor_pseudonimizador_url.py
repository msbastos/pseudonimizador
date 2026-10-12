# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
r"""Pseudonimizador 0.5.0, Task 6: URL com nome de pessoa vira um tóken
[[URL_n]] inteiro.

Caso de producao (28/09/2026): uma contestacao citava o perfil do LinkedIn
da reclamante — "linkedin.com/in/<prenome>-<sobrenome>-" com a quebra de
linha do PDF antes do numero do perfil. O slug era minusculo e ligado por
hifen: nem o nome completo (so' espaco separa as palavras de um nome) nem
o prenome isolado (so' com maiuscula) o trocavam. A guarda, que compara
sem caixa, parou a sessao.

Regras que estes testes trancam (as do cetico que refutou a 1a versao):
  - a URL (http(s):// ou www.) vira [[URL_n]] (categoria 'url') quando os
    trechos em letras dela tem palavra de nome de pessoa do mapa, ou
    quando e' perfil pessoal (linkedin.com/in/, instagram.com/,
    facebook.com/, tiktok.com/@, x.com/, twitter.com/, wa.me/); URL
    institucional sem nome (jus.br, gov.br) fica;
  - a continuacao na linha seguinte so' quando ela comeca por pontuacao de
    URL, por digito depois da URL partida em pontuacao (a data depois da
    URL inteira fica), e' toda minuscula sem espaco, ou e' o resto do slug
    com hifen depois do slug partido em "-" — NUNCA a palavra com
    maiuscula sem hifen: o nome da parte na linha de baixo e' trocado como
    nome, e os sobrenomes dele nao ficam em claro;
  - no dominio institucional, so' o perfil pessoal ou 2+ palavras do nome
    da mesma pessoa; o [[PRENOME_n]] nunca nasce dentro da URL; na guarda,
    as excecoes de uma palavra sao so' da categoria 'pessoa';
  - o nome que comeca dentro da URL e termina fora corta a URL antes dele;
  - a reversao devolve a URL exata; a guarda e o filtro de saida a vigiam;
    a classe da URL nao engole aspas, barra invertida (o JSON do dossie) nem
    '|' (a tabela do resumo).
Residuais documentados (docs/privacidade.md): URL sem esquema e sem www,
slug colado ("joanakretzer"), quebra no meio da palavra. Revisao final
(29/09/2026): a guarda ve tambem o nome ligado por '_' ("@joana_kretzer_lopes",
"instagram.com/joana_kretzer", "procuracao_joana.pdf") — '_' e' \w, e os
limites de palavra da guarda nao casavam; antes so' o hifen valia.

Nomes inventados.

Rodar:  python -X utf8 testes/test_pseudonimizador_url.py
"""
import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pseudonimizador.motor.mapa import token_para  # noqa: E402
from pseudonimizador.motor.pseudonimizador import pseudonimizar  # noqa: E402
from pseudonimizador.motor.reversor import despseudonimizar_texto  # noqa: E402


def _mapa():
    m = {"schema_version": 1, "cnj": "x", "criado_em": "", "tokens": {}}
    token_para(m, "RECLAMANTE", "pessoa", "JOANA KRETZER LOPES", papel="Reclamante")
    return m


def test_url_com_nome_do_mapa_vira_um_tokien_inteiro_e_volta_exata():
    m = _mapa()
    url = "https://www.linkedin.com/in/joana-kretzer-\n1234567/?utm_source=share"
    t = pseudonimizar(f"Perfil: {url} (acesso em 2024)", m)
    assert t == "Perfil: [[URL_1]] (acesso em 2024)", repr(t)
    assert m["tokens"]["[[URL_1]]"] == {"valor": url, "categoria": "url"}, m["tokens"]["[[URL_1]]"]
    assert despseudonimizar_texto(t, m) == f"Perfil: {url} (acesso em 2024)"
    t = pseudonimizar("ver https://www.linkedin.com/in/Joana-Kretzer-1234567/.", m)
    assert t == "ver [[URL_2]].", t
    t = pseudonimizar("site https://kretzer-lima-advogados.exemplo.com.br/ ", m)
    assert t == "site [[URL_3]] ", t


def test_perfil_pessoal_vira_tokien_e_url_institucional_fica():
    m = _mapa()
    t = pseudonimizar("https://www.instagram.com/fulano.beltrano/ e https://x.com/qualquer e "
                      "https://wa.me/5551999999999", m)
    assert t == "[[URL_1]] e [[URL_2]] e [[URL_3]]", t
    for fica in ("https://www.webex.com/meet/sala-12", "https://www.trt4.jus.br/portais/trt4",
                 "www.gov.br/trabalho-e-emprego"):
        assert pseudonimizar(f"acesse {fica} hoje", m) == f"acesse {fica} hoje", fica


def test_url_nao_engole_o_nome_da_linha_seguinte():
    # testes obrigatorios do cetico: com a continuacao cega, o nome da linha
    # de baixo entrava na URL e os sobrenomes ficavam em claro, sem a guarda ver
    m = _mapa()
    for texto in ("Site: https://www.escritorio.com.br/\nJOANA KRETZER LOPES, brasileira",
                  "Fonte: https://www.trt4.jus.br.\nJOANA KRETZER LOPES, brasileira",
                  "https://www.linkedin.com/in/joana-kretzer-\nJOANA KRETZER LOPES, brasileira",
                  "https://www.site.com.br/perfil?id=\nJoana Kretzer Lopes, brasileira"):
        t = pseudonimizar(texto, m)
        assert "KRETZER" not in t.upper().replace("[[URL", "") and "LOPES" not in t.upper(), repr(t)
        assert "[[RECLAMANTE_1]], brasileira" in t, repr(t)


def test_continuacao_do_slug_com_hifen_e_a_data_da_linha_seguinte():
    m = _mapa()
    # o slug partido no hifen continua na linha de baixo com maiuscula: entra na URL
    url = "https://www.linkedin.com/in/joana-\nKretzer-Lopes-123"
    t = pseudonimizar(f"Perfil: {url} (acesso em 2024).", m)
    assert t == "Perfil: [[URL_1]] (acesso em 2024).", repr(t)
    assert m["tokens"]["[[URL_1]]"]["valor"] == url
    # a data na linha de baixo, depois da URL inteira (sem pontuacao no fim), nao
    t = pseudonimizar("perfil https://www.facebook.com/perfil.qualquer\n10/05/2023 - a reclamante postou", m)
    assert t == "perfil [[URL_2]]\n10/05/2023 - a reclamante postou", repr(t)
    t = pseudonimizar("ver https://www.site.com.br/joana.\n2023 foi o ano", m)
    assert t == "ver [[URL_3]].\n2023 foi o ano", repr(t)


def test_dominio_institucional_exige_duas_palavras_da_mesma_pessoa():
    m = {"schema_version": 1, "cnj": "x", "criado_em": "", "tokens": {}}
    token_para(m, "RECLAMANTE", "pessoa", "Fulana Terciana Campos", papel="Reclamante")
    for fica in ("https://www.trt4.jus.br/portais/campos/noticia", "https://www.gov.br/trabalho/campos-gerais"):
        assert pseudonimizar(f"Ver {fica} hoje", m) == f"Ver {fica} hoje", fica
    assert pseudonimizar("Ver https://www.trt4.jus.br/pauta/fulana-campos hoje", m) == "Ver [[URL_1]] hoje"
    assert pseudonimizar("Ver https://www.exemplo.com.br/campos hoje", m) == "Ver [[URL_2]] hoje"


def test_prenome_ambiguo_nunca_nasce_dentro_da_url():
    m = _mapa()
    token_para(m, "RECLAMADO", "pessoa", "JOANA PAES LIMA", papel="Reclamado")
    t = pseudonimizar("fotos em https://www.exemplo.com.br/Joana/fotos e Joana disse", m)
    assert t == "fotos em [[URL_1]] e [[PRENOME_1]] disse", t
    assert m["tokens"]["[[PRENOME_1]]"]["valor"] == "Joana" and "[[PRENOME_2]]" not in m["tokens"]
    m = _mapa()
    token_para(m, "RECLAMADO", "pessoa", "JOANA PAES LIMA", papel="Reclamado")
    assert pseudonimizar("fotos em https://www.exemplo.com.br/Joana/fotos", m) == "fotos em [[URL_1]]"
    assert not [t for t in m["tokens"] if t.startswith("[[PRENOME_")], list(m["tokens"])


def test_nome_que_comeca_dentro_da_url_e_termina_fora_corta_a_url():
    m = _mapa()
    t = pseudonimizar("em https://www.site.com.br/Joana Kretzer Lopes consta", m)
    assert t == "em https://www.site.com.br/[[RECLAMANTE_1]] consta", t


def test_url_no_json_e_na_tabela_do_resumo():
    m = _mapa()
    t = pseudonimizar(json.dumps({"d": "https://www.linkedin.com/in/joana-kretzer/", "n": 1}), m)
    assert json.loads(t) == {"d": "[[URL_1]]", "n": 1}, t
    t = pseudonimizar("| 3 | https://www.linkedin.com/in/joana-kretzer | 3-3 |", m)
    assert t == "| 3 | [[URL_2]] | 3-3 |", t


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
