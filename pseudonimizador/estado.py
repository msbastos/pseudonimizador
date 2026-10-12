# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Pasta de estado do aplicativo (%LOCALAPPDATA%\\Pseudonimizador, ou a
variável PSEUDONIMIZADOR_ESTADO), a configuração (config.json) e o log do
servidor. Nada aqui lê ou grava conteúdo de documento."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from .motor.mapa import escrever_atomico

ARQUIVO_CONFIG = "config.json"
FORMATOS = ("layout", "texto")
TIPOS = ("docx", "pdf")
MODOS = ("reversivel", "definitivo")


def pasta_estado() -> Path:
    env = os.environ.get("PSEUDONIMIZADOR_ESTADO")
    if env:
        return Path(env)
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "Pseudonimizador"


def pasta_base_padrao() -> Path:
    return Path(os.environ.get("USERPROFILE") or Path.home()) / "Documents" / "Pseudonimizador"


@dataclass
class Config:
    pasta_base: str
    pasta_saida: str = ""        # vazio: <pasta_base>\Saida
    pasta_mapas: str = ""        # vazio: <pasta_base>\Mapas
    formato: str = "layout"      # padrões do lote (pasta Entrada)
    tipo: str = "docx"           # só para formato "texto"
    modo: str = "reversivel"

    @property
    def entrada(self) -> Path:
        return Path(self.pasta_base) / "Entrada"

    @property
    def processados(self) -> Path:
        return self.entrada / "Processados"

    @property
    def saida(self) -> Path:
        return Path(self.pasta_saida) if self.pasta_saida else Path(self.pasta_base) / "Saida"

    @property
    def mapas(self) -> Path:
        return Path(self.pasta_mapas) if self.pasta_mapas else Path(self.pasta_base) / "Mapas"

    def pastas(self) -> dict[str, str]:
        return {"entrada": str(self.entrada), "saida": str(self.saida), "mapas": str(self.mapas),
                "processados": str(self.processados)}


def _raiz_da_instalacao() -> Path | None:
    """A pasta do programa instalado (a que o desinstalador apaga). Num clone do repositório
    (desenvolvimento, testes) não há desinstalador: devolve None."""
    raiz = Path(__file__).resolve().parents[1]
    return None if (raiz / ".git").exists() else raiz


def validar(dados: dict) -> Config:
    """Config a partir de um dicionário (o JSON do disco ou o corpo da tela).
    ValueError com a frase para o usuário. As regras que o `gerar` já aplica
    (mapas nunca na saída nem dentro dela, e vice-versa) são recusadas aqui,
    antes de gravar."""
    if not isinstance(dados, dict):
        raise ValueError("configuração inválida")
    base = str(dados.get("pasta_base") or "").strip()
    if not base:
        raise ValueError("informe a pasta base")
    if not Path(base).is_absolute():
        raise ValueError("pasta base: informe o caminho completo")
    cfg = Config(pasta_base=base,
                 pasta_saida=str(dados.get("pasta_saida") or "").strip(),
                 pasta_mapas=str(dados.get("pasta_mapas") or "").strip(),
                 formato=str(dados.get("formato") or "layout"),
                 tipo=str(dados.get("tipo") or "docx"),
                 modo=str(dados.get("modo") or "reversivel"))
    for campo, aceitos in (("formato", FORMATOS), ("tipo", TIPOS), ("modo", MODOS)):
        if getattr(cfg, campo) not in aceitos:
            raise ValueError(f"{campo} inválido: escolha entre {', '.join(aceitos)}")
    for campo, rotulo in (("pasta_saida", "pasta de saída"), ("pasta_mapas", "pasta dos mapas")):
        valor = getattr(cfg, campo)
        if valor and not Path(valor).is_absolute():
            raise ValueError(f"{rotulo}: informe o caminho completo")
    try:
        s, m, e = cfg.saida.resolve(), cfg.mapas.resolve(), cfg.entrada.resolve()
    except (OSError, ValueError, RuntimeError) as erro:
        raise ValueError(f"caminho inválido: {erro.strerror or erro}") from None
    # O desinstalador apaga a pasta do programa e, se o usuário disser sim, a do estado: os arquivos
    # do usuário nunca podem morar dentro delas.
    try:
        instalacao = _raiz_da_instalacao()
        guardado = pasta_estado().resolve()
        base_r = Path(cfg.pasta_base).resolve()
    except (OSError, ValueError, RuntimeError) as erro:
        raise ValueError(f"caminho inválido: {erro.strerror or erro}") from None
    for rotulo, p in (("pasta base", base_r), ("pasta de saída", s), ("pasta dos mapas", m)):
        for nome, protegida in (("da instalação do programa", instalacao), ("de estado do programa", guardado)):
            if protegida is None:
                continue
            if p == protegida or protegida in p.parents:
                raise ValueError(f"{rotulo}: não pode ser a pasta {nome} nem ficar dentro dela "
                                 f"(o desinstalador apagaria seus arquivos); escolha outra, como Documentos")
    # A pasta vigiada (Entrada) não pode ver saídas e mapas como se fossem entradas.
    if any(x == e or x in e.parents or e in x.parents for x in (s, m)):
        raise ValueError("a saída e os mapas não podem ser a pasta Entrada nem ficar dentro dela (ou vice-versa)")
    if s == m or s in m.parents or m in s.parents:
        raise ValueError("a pasta dos mapas não pode ser a da saída nem ficar dentro dela (ou vice-versa)")
    return cfg


def carregar(pasta_estado: Path) -> Config:
    """A config gravada; sem arquivo, a padrão. Arquivo corrompido vira
    config.json.bak (nada bloqueia a abertura) e volta-se à padrão; erro de
    leitura (OSError) só volta à padrão, sem renomear."""
    arquivo = Path(pasta_estado) / ARQUIVO_CONFIG
    padrao = Config(pasta_base=str(pasta_base_padrao()))
    if not arquivo.is_file():
        return padrao
    try:
        return validar(json.loads(arquivo.read_text(encoding="utf-8")))
    except ValueError:                 # conteúdo corrompido: guarda como .bak
        try:
            os.replace(arquivo, arquivo.with_suffix(".json.bak"))
        except OSError:
            pass
        return padrao
    except OSError:                    # trava passageira: não descarta uma config que pode estar boa
        return padrao


def gravar(pasta_estado: Path, config: Config) -> None:
    escrever_atomico(Path(pasta_estado) / ARQUIVO_CONFIG, json.dumps(asdict(config), ensure_ascii=False, indent=1))


def preparar_pastas(config: Config) -> None:
    for pasta in (config.entrada, config.processados, config.saida, config.mapas):
        pasta.mkdir(parents=True, exist_ok=True)


def abrir_log(pasta_estado: Path) -> logging.Logger:
    """Logger próprio (não o do registro global: cada Aplicacao tem o seu e o
    fecha ao encerrar). Quem escreve nele nunca passa valor nem nome de arquivo."""
    pasta = Path(pasta_estado) / "logs"
    pasta.mkdir(parents=True, exist_ok=True)
    log = logging.Logger("pseudonimizador.servidor", logging.INFO)
    h = logging.FileHandler(pasta / "servidor.log", encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(h)
    return log
