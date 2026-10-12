# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Pasta de estado, config.json e log do servidor."""
import _base  # noqa: F401
import json
import os
from pathlib import Path

import fabrica as F
from pseudonimizador import estado
from pseudonimizador.estado import Config, abrir_log, carregar, gravar, preparar_pastas, validar


def test_pasta_estado_pela_variavel_de_ambiente():
    pasta = F.pasta_temporaria("estado_env")
    os.environ["PSEUDONIMIZADOR_ESTADO"] = str(pasta)
    try:
        assert estado.pasta_estado() == pasta
    finally:
        del os.environ["PSEUDONIMIZADOR_ESTADO"]
    padrao = estado.pasta_estado()
    assert padrao.name == "Pseudonimizador" and padrao.is_absolute()


def test_config_padrao_gravar_carregar_e_pastas():
    pasta = F.pasta_temporaria("estado_cfg")
    cfg = carregar(pasta)
    assert cfg == Config(pasta_base=str(estado.pasta_base_padrao()))
    nova = Config(pasta_base=str(pasta / "Base"), formato="texto", tipo="pdf", modo="definitivo")
    gravar(pasta, nova)
    assert json.loads((pasta / "config.json").read_text(encoding="utf-8"))["modo"] == "definitivo"
    assert carregar(pasta) == nova
    preparar_pastas(nova)
    for sub in ("Entrada", "Entrada/Processados", "Saida", "Mapas"):
        assert (pasta / "Base" / sub).is_dir()
    assert nova.pastas() == {"entrada": str(pasta / "Base" / "Entrada"), "saida": str(pasta / "Base" / "Saida"),
                             "mapas": str(pasta / "Base" / "Mapas"),
                             "processados": str(pasta / "Base" / "Entrada" / "Processados")}


def test_validar_recusa_o_que_a_tela_nao_pode_gravar():
    base = str(Path(F.pasta_temporaria("estado_val")) / "Base")
    assert validar({"pasta_base": base}).modo == "reversivel"
    casos = [
        ({}, "pasta base"),
        ({"pasta_base": "Base"}, "caminho completo"),
        ({"pasta_base": base, "modo": "talvez"}, "modo"),
        ({"pasta_base": base, "formato": "foto"}, "formato"),
        ({"pasta_base": base, "tipo": "txt"}, "tipo"),
        ({"pasta_base": base, "pasta_mapas": base + "\\Saida\\M"}, "mapas"),
        ({"pasta_base": base, "pasta_saida": base + "\\Mapas"}, "mapas"),
        ({"pasta_base": base, "pasta_saida": base + "\\Entrada"}, "Entrada"),
        ({"pasta_base": base, "pasta_saida": "Saida"}, "caminho completo"),
        ({"pasta_base": base, "pasta_saida": base + "/Entrada/Fora"}, "Entrada"),
        ({"pasta_base": base, "pasta_mapas": base + "/Entrada/M"}, "Entrada"),
        ({"pasta_base": base + "/Entrada/Sub", "pasta_saida": base + "/Entrada"}, "Entrada"),
        ({"pasta_base": base + "/Entrada/Sub", "pasta_mapas": base}, "Entrada"),
    ]
    for dados, trecho in casos:
        try:
            validar(dados)
        except ValueError as e:
            assert trecho in str(e), (dados, str(e))
        else:
            raise AssertionError(f"deveria recusar {dados}")


def test_config_ilegivel_vira_bak_e_volta_ao_padrao():
    pasta = F.pasta_temporaria("estado_bak")
    (pasta / "config.json").write_text("{{{", encoding="utf-8")
    assert carregar(pasta).pasta_base == str(estado.pasta_base_padrao())
    assert (pasta / "config.json.bak").is_file() and not (pasta / "config.json").exists()


def test_validar_converte_erro_de_resolve_em_caminho_invalido():
    base = str(Path(F.pasta_temporaria("estado_res")) / "Base")
    original = Path.resolve

    def estoura(self, *a, **k):
        raise OSError(22, "nome reservado")
    Path.resolve = estoura
    try:
        validar({"pasta_base": base})
    except ValueError as e:
        assert "caminho inválido" in str(e)
    else:
        raise AssertionError("deveria recusar")
    finally:
        Path.resolve = original


def test_config_ilegivel_por_erro_de_leitura_nao_e_renomeada():
    pasta = F.pasta_temporaria("estado_lock")
    (pasta / "config.json").write_text("{}", encoding="utf-8")
    original = Path.read_text

    def trava(self, *a, **k):
        if self.name == "config.json":
            raise PermissionError("trava")
        return original(self, *a, **k)
    Path.read_text = trava
    try:
        cfg = carregar(pasta)
    finally:
        Path.read_text = original
    assert cfg.pasta_base == str(estado.pasta_base_padrao())
    assert (pasta / "config.json").is_file() and not (pasta / "config.json.bak").exists()


def test_log_grava_na_pasta_de_estado():
    pasta = F.pasta_temporaria("estado_log")
    log = abrir_log(pasta)
    log.info("evento %d", 7)
    for h in list(log.handlers):
        h.close()
    texto = (pasta / "logs" / "servidor.log").read_text(encoding="utf-8")
    assert "evento 7" in texto and "INFO" in texto


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
