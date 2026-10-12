# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Configurações pela janela: ler, gravar, validar antes de gravar, e o gerar usa o novo."""
import _base  # noqa: F401
import json

import fabrica as F
from _web import ServidorDeTeste


def test_config_ler_gravar_validar_e_usar():
    with ServidorDeTeste("web_config") as s:
        status, c = s.get("/api/config")
        assert status == 200 and c["pasta_base"] == str(s.pasta / "Base") and c["formato"] == "layout"
        assert c["pastas"]["entrada"] == str(s.pasta / "Base" / "Entrada") and c["pasta_saida"] == ""
        nova = {"pasta_base": str(s.pasta / "Base2"), "formato": "texto", "tipo": "pdf", "modo": "definitivo"}
        status, c = s.post("/api/config", nova)
        assert status == 200 and c["modo"] == "definitivo" and c["pastas"]["saida"] == str(s.pasta / "Base2" / "Saida")
        for sub in ("Entrada", "Saida", "Mapas", "Entrada/Processados"):
            assert (s.pasta / "Base2" / sub).is_dir()
        gravado = json.loads((s.pasta / "estado" / "config.json").read_text(encoding="utf-8"))
        assert gravado["pasta_base"] == str(s.pasta / "Base2") and gravado["tipo"] == "pdf"
        # mapas dentro da saída: recusado ANTES de gravar
        status, e = s.post("/api/config", {**nova, "pasta_mapas": str(s.pasta / "Base2" / "Saida" / "M")})
        assert status == 400 and e["erro"] == "config" and "mapas" in e["mensagem"]
        assert s.get("/api/config")[1]["pasta_mapas"] == ""
        assert s.post("/api/config", {**nova, "pasta_base": "Base3"})[0] == 400
        assert s.post("/api/config", {**nova, "modo": "talvez"})[0] == 400
        assert s.post("/api/config", b"x")[0] == 400
        # saída dentro da Entrada: 400 com a frase da regra
        status, e = s.post("/api/config", {**nova, "pasta_saida": str(s.pasta / "Base2" / "Entrada" / "Fora")})
        assert status == 400 and e["erro"] == "config" and "Entrada" in e["mensagem"]
        # caractere inválido (byte nulo): 400, nunca 500
        assert s.post("/api/config", {**nova, "pasta_saida": "C:/x/a\0b"})[0] == 400
        # o gerar com corpo vazio passa a usar os padrões e as pastas novas
        status, r = s.enviar_arquivo(F.contrato_docx(s.pasta / "contrato.docx"))
        s.esperar(r["id"], "revisao")
        assert s.post(f"/api/documentos/{r['id']}/gerar", {})[0] == 202
        d = s.esperar(r["id"], "pronto", "erro")
        assert d["situacao"] == "pronto", d["erro"]
        assert d["resultado"]["saida_nome"] == "contrato - anonimizado.pdf" and d["resultado"]["mapa_nome"] is None
        assert (s.pasta / "Base2" / "Saida" / "contrato - anonimizado.pdf").is_file()
    assert s.pasta.name not in s.log_texto()       # o caminho não vai ao log


def test_config_falha_ao_gravar_responde_409_e_nada_aplica():
    from pseudonimizador.web import servidor
    with ServidorDeTeste("web_config_gravar") as s:
        original = servidor.gravar

        def nega(*a, **k):
            raise PermissionError("negado")
        servidor.gravar = nega
        try:
            status, e = s.post("/api/config", {"pasta_base": str(s.pasta / "Base2")})
        finally:
            servidor.gravar = original
        assert status == 409 and e["erro"] == "config" and "não foi possível gravar as configurações" in e["mensagem"]
        assert s.get("/api/config")[1]["pasta_base"] == str(s.pasta / "Base")
        assert not (s.pasta / "estado" / "config.json").exists()


def test_pastas_inacessiveis_na_abertura_o_app_sobe_e_avisa():
    """Disco da pasta base ausente: preparar_pastas falha na abertura; o app
    sobe, /api/estado avisa, gerar/restaurar dão 409 e salvar uma pasta boa conserta."""
    import pseudonimizador.web.servidor as srv
    original = srv.preparar_pastas
    chamadas = []

    def falha_na_abertura(cfg):
        chamadas.append(1)
        if len(chamadas) == 1:
            raise FileNotFoundError("disco ausente")
        return original(cfg)
    srv.preparar_pastas = falha_na_abertura
    try:
        with ServidorDeTeste("web_cfg_ausente") as s:
            status, e = s.get("/api/estado")
            assert status == 200 and e["pastas_disponiveis"] is False
            assert "FileNotFoundError" in s.log_texto() and "disco ausente" not in s.log_texto()
            assert s.post("/api/documentos/" + "a" * 16 + "/gerar", {})[1]["erro"] in ("pastas", "documento")
            nova = dict(s.get("/api/config")[1])
            nova["pasta_base"] = str(s.pasta / "BaseBoa")
            status, r = s.post("/api/config", nova)
            assert status == 200, r
            assert s.get("/api/estado")[1]["pastas_disponiveis"] is True
    finally:
        srv.preparar_pastas = original


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
