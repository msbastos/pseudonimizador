# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""O que entra no pacote instalado em {app} (spec §2): o código (pseudonimizador/,
com os .json do léxico e os estáticos da janela), LICENSE, CREDITOS.md e README.md.
Não entra: testes, saída de testes, docs, .bat, requirements, empacotamento,
caches, config/instância/log de uma execução, qualquer mapa ou documento."""
from __future__ import annotations

from pathlib import Path

# (pasta ou arquivo relativo à raiz, recursivo?)
INCLUIR: tuple[tuple[str, bool], ...] = (("LICENSE", False), ("CREDITOS.md", False), ("README.md", False),
                                         ("pseudonimizador", True))
PASTAS_EXCLUIDAS = frozenset({"__pycache__", ".git", ".claude", "testes", "saida_testes"})
SUFIXOS_EXCLUIDOS = frozenset({".pyc", ".pyo", ".bat", ".log", ".pdf", ".docx", ".tmp", ".bak"})
# lista fechada: sob pseudonimizador/ só estes sufixos viajam; na raiz, só os três arquivos de INCLUIR
SUFIXOS_PERMITIDOS = frozenset({".py", ".json", ".css", ".js", ".html"})
NOMES_EXCLUIDOS = frozenset({"config.json", "instancia.json", ".env"})
# o que, se aparecer na lista final, é erro da montagem (nunca viaja); comparado ao caminho POSIX com "/" nas pontas
PROIBIDOS_NO_CAMINHO = ("/superpowers/", "/saida_testes/", "/Mapas/", "/Entrada/", "/Saida/", "/termos_proibidos.txt",
                        "/config.json", "/instancia.json", "/revisao.json")


def _aceito(rel: Path) -> bool:
    if any(parte in PASTAS_EXCLUIDAS for parte in rel.parts[:-1]):
        return False
    return (rel.suffix.lower() in SUFIXOS_PERMITIDOS and rel.suffix.lower() not in SUFIXOS_EXCLUIDOS
            and rel.name not in NOMES_EXCLUIDOS)


def arquivos_do_pacote(raiz: Path) -> list[Path]:
    """Caminhos relativos a `raiz`, ordenados, só os que existem."""
    raiz = Path(raiz)
    achados: set[Path] = set()
    for entrada, recursivo in INCLUIR:
        alvo = raiz / entrada
        if not alvo.exists():
            continue
        if alvo.is_file():
            achados.add(Path(entrada))
            continue
        for p in (alvo.rglob("*") if recursivo else alvo.glob("*")):
            if p.is_file():
                rel = p.relative_to(raiz)
                if _aceito(rel):
                    achados.add(rel)
    return sorted(achados, key=lambda p: p.as_posix())


def _fora_da_lista(rel: Path) -> bool:
    if len(rel.parts) == 1:
        return rel.as_posix() not in {e for e, _ in INCLUIR}
    return rel.parts[0] != "pseudonimizador" or rel.suffix.lower() not in SUFIXOS_PERMITIDOS


def _mapa_fora_do_motor(rel: Path) -> bool:
    nome = rel.name.lower()
    if "mapa_pseudonimos" in nome:
        return True
    return nome.startswith("mapa") and nome.endswith(".json") and rel.parts[:2] != ("pseudonimizador", "motor")


def problemas(relativos: list[Path]) -> list[str]:
    """Uma mensagem por arquivo que nunca pode viajar (lista vazia = ok). A
    comparação ignora a caixa; o pacote real pseudonimizador/saida/ é código."""
    saida = []
    for rel in relativos:
        rel = Path(rel)
        texto = "/" + rel.as_posix().lower()
        motivo = None
        for proibido in PROIBIDOS_NO_CAMINHO:
            if proibido.lower() in texto and not (proibido == "/Saida/" and texto.startswith("/pseudonimizador/saida/")):
                motivo = f"contém '{proibido.strip('/')}'"
                break
        if motivo is None and _fora_da_lista(rel):
            motivo = "fora da lista fechada de arquivos do pacote"
        if motivo is None and _mapa_fora_do_motor(rel):
            motivo = "parece mapa de pseudônimos"
        if motivo:
            saida.append(f"não pode entrar no pacote: {rel.as_posix()} ({motivo})")
    return saida
