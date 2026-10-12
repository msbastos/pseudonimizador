# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
# Origem: Ulpiano, ulpiano/nucleo/privacidade/nivel.py, commit 5bab2ff (11/10/2026); alterações descritas abaixo.
"""Nivel de protecao do dossie (decisao de 04/10/2026).

O processo judicial e' publico: o nome de quem litiga nao e' segredo.
Protege-se o processo sigiloso (nomes de pessoas e de empresas em codigo),
o que tem menor ou dado sensivel ligado 'a pessoa (nomes de pessoas em
codigo, como sempre foi) — e, em todos, os documentos e contatos.

  sigiloso   marca de sigilo/segredo de justica, ou pedido do juiz
  protegido  menor, dado sensivel, configuracao "sempre", pedido do juiz,
             ou a regra nao pode avaliar (na duvida, o mais protetivo)
  publico    os demais: nomes em claro; identificadores e contatos em codigo;
             o documento referente a menor (certidao de nascimento...) vai
             sozinho com os nomes em codigo (documento_de_menor, elevado)

Em todo nivel, o documento juntado referente a menor tem o rotulo cortado
(rotulo_do_documento_de_menor) e o nome da crianca do titulo
(nomes_no_rotulo_de_menor, quando e' nome) em codigo no texto dele.

Calibracao do juiz (04/10/2026): ASO e exame ocupacional nao protegem; o
indice sem as partes da capa nao protege; o documento de menor nao sobe o
processo (o menor que e' parte, na inicial, continua subindo).

A regra e' local e deterministica (os sinais ficam em nivel_sinais.json).
O nivel viaja no mapa de pseudonimos (mapa["nivel"]): o pseudonimizador,
a guarda de entrada e o filtro de saida o leem de la'. Os motivos sao
rotulos fixos — nunca nome, numero ou trecho dos autos.
"""
from __future__ import annotations

import json
import re
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

SIGILOSO, PROTEGIDO, PUBLICO = "sigiloso", "protegido", "publico"
NIVEIS = (PUBLICO, PROTEGIDO, SIGILOSO)          # do menos ao mais protetivo
NOMES = ("regra", "sempre")                      # [privacidade] nomes
NOME_PEDIDO = "nivel_protecao.json"              # na raiz da pasta do processo, no acervo
NOME_RESULTADO = "nivel.json"                    # na pasta da execucao do dossie
TIPOS_DA_INICIAL = ("peticao_inicial", "emenda_inicial", "emenda")

M_SIGILO = "marca de sigilo ou segredo de justiça na capa"
M_PEDIDO = "pedido do juiz"
M_SEMPRE = "configuração: sempre trocar os nomes"
M_SEM_AVALIACAO = "não foi possível avaliar o processo"
M_SEM_INICIAL = "petição inicial não encontrada"
M_DOCUMENTO = "documento médico nos autos"
M_MENOR = "há menor no processo"
_ARQUIVO_SINAIS = Path(__file__).with_name("nivel_sinais.json")


def _carregar_sinais() -> dict:
    bruto = json.loads(_ARQUIVO_SINAIS.read_text(encoding="utf-8"))

    def junta(padroes):
        return re.compile("|".join(f"(?:{p})" for p in padroes), re.I)
    return {"versao": int(bruto["versao"]),
            "minimo": int(bruto["minimo_de_mencoes_do_pedido"]),
            "documento": junta(bruto["documento_medico"]),
            "documento_de_menor": junta(bruto["documento_de_menor"]),
            "pedidos": {rotulo: junta(ps) for rotulo, ps in bruto["pedidos"].items()},
            "menor": junta(bruto["menor"])}


SINAIS = _carregar_sinais()
MOTIVOS_POSSIVEIS = (M_SIGILO, M_PEDIDO, M_SEMPRE, M_SEM_AVALIACAO, M_SEM_INICIAL, M_DOCUMENTO, M_MENOR,
                     *(f"a inicial discute {r}" for r in SINAIS["pedidos"]))


@dataclass(frozen=True)
class Nivel:
    nome: str
    motivos: tuple[str, ...] = ()


def mais_alto(a: str, b: str) -> str:
    return max(a, b, key=NIVEIS.index)


def abaixo_do_pedido(nivel: str | None, pedido: str | None) -> bool:
    """O nivel montado (None ou desconhecido: protegido, como na copia a' Pasta do Claude) esta' abaixo do que o
    juiz pediu: o dossie ainda nao foi preparado com a protecao pedida e nao vai ao Claude."""
    if pedido not in (PROTEGIDO, SIGILOSO):
        return False
    montado = nivel if nivel in NIVEIS else PROTEGIDO
    return mais_alto(pedido, montado) != montado


def nomes_em_codigo(nivel: str | None) -> bool:
    return nivel != PUBLICO


def empresas_em_codigo(nivel: str | None) -> bool:
    return nivel == SIGILOSO


def do_mapa(mapa: dict | None) -> str:
    """Documento avulso: sempre sigiloso (nomes e empresas em código; spec §2)."""
    return SIGILOSO


def tokens_vigiados(mapa: dict | None) -> dict:
    """Os tokens do mapa que a guarda de entrada, o filtro de saida e a retencao por palavra vigiam. Um mapa
    de rodada anterior, de outro nivel, pode trazer o que o nivel de agora deixa em claro, e esse codigo nao
    pode travar a guarda nem o filtro: em publico ficam de fora os de pessoa e os de URL que so' eram trocadas
    por trazer um nome (a de perfil pessoal segue vigiada); fora de sigiloso, os de empresa ('pj')."""
    tokens = (mapa or {}).get("tokens") or {}
    nivel = do_mapa(mapa)
    if nivel == SIGILOSO:
        return dict(tokens)
    if nomes_em_codigo(nivel):
        return {t: i for t, i in tokens.items() if not (isinstance(i, dict) and i.get("categoria") == "pj")}
    # import tardio: o pseudonimizador importa este modulo no topo
    from .pseudonimizador import RE_PERFIL_PESSOAL

    def em_claro(i) -> bool:
        if not isinstance(i, dict):
            return False
        categoria = i.get("categoria")
        return (categoria in ("pessoa", "pj")
                or (categoria == "url" and not RE_PERFIL_PESSOAL.search(str(i.get("valor") or ""))))
    return {t: i for t, i in tokens.items() if not em_claro(i)}


def _titulo(doc: dict) -> str:
    return " ".join(str(doc.get(k) or "") for k in ("descricao", "titulo_bruto", "tipo_oficial"))


# O documento juntado (anexo, prova): os tipos canonicos da taxonomia (segmentador/taxonomia.py) de documento, os
# genericos ("Documento Diverso", "Certidão", o tipo sem regra) e o indice sem tipo. Fora: toda peca processual
# (inicial, contestacao, manifestacao, recurso...) e todo ato do juizo (sentenca, decisao, despacho, ata) — a
# inicial que pede o salario-familia nao e' documento de menor (rodada de correcao 1 da Task 11).
TIPOS_DE_DOCUMENTO_JUNTADO = frozenset({"documento_anexo", "documento_diverso", "documento_tecnico_sst", "fotografia",
                                        "certidao", "outros", None})


def documento_de_menor(doc: dict) -> bool:
    """O documento juntado referente a menor (certidao de nascimento, salario-familia, caderneta de vacina, termo de
    guarda, declaracao de dependentes), pela descricao, pelo titulo do PJe ou pelo tipo oficial; o tipo do indice
    tem de ser de documento juntado (TIPOS_DE_DOCUMENTO_JUNTADO). Calibracao do juiz (04/10/2026): "apenas o
    documento referente ao menor" — a montagem trata so' ele, em todo nivel (rotulo_do_documento_de_menor; no
    publico, o texto dentro de elevado)."""
    doc = doc or {}
    return doc.get("tipo") in TIPOS_DE_DOCUMENTO_JUNTADO and bool(SINAIS["documento_de_menor"].search(_titulo(doc)))


def _com_letra(texto: str) -> bool:
    return any(c.isalpha() for c in texto)


def rotulo_de_menor(texto: str | None) -> str | None:
    """O rotulo do documento de menor so' com o trecho que casou o sinal e, havendo alguma letra antes ou depois
    dele, " [nome omitido]" ("Fulaninho - Certidao de nascimento" e "Certidao de nascimento - Fulaninho" ->
    "Certidao de nascimento [nome omitido]"; "CERTIDAO DE NASCIMENTO 2" -> "CERTIDAO DE NASCIMENTO"). O texto que
    nao casa volta como veio."""
    if not texto:
        return texto
    m = SINAIS["documento_de_menor"].search(texto)
    if m is None:
        return texto
    return m.group(0) + (" [nome omitido]" if _com_letra(texto[:m.start()] + texto[m.end():]) else "")


def rotulo_do_documento_de_menor(texto: str | None) -> str | None:
    """Cada campo de rotulo (tipo oficial, descricao, titulo do PJe) do documento de menor: o que traz o sinal, por
    rotulo_de_menor; o que nao o traz (o nome sozinho na descricao, o tipo oficial generico) vira "[nome omitido]"
    quando tem alguma letra."""
    if not texto or SINAIS["documento_de_menor"].search(texto):
        return rotulo_de_menor(texto)
    return "[nome omitido]" if _com_letra(texto) else texto


def nomes_no_rotulo_de_menor(texto: str | None) -> list[str]:
    """O que o corte do rotulo tira, candidato a nome da crianca: o texto antes e o depois do sinal, sem a
    pontuacao das pontas ("Fulaninho de Tal - Certidao de nascimento" -> ["Fulaninho de Tal"]), ou o campo
    inteiro sem o sinal; so' o que tem letra. Se e' nome, confere o pseudonimizador, sem olhar a caixa
    (descobrir_nome_do_rotulo)."""
    if not texto:
        return []
    m = SINAIS["documento_de_menor"].search(texto)
    partes = [texto[:m.start()], texto[m.end():]] if m else [texto]
    limpas = (re.sub(r"^[\W_]+|[\W_]+$", "", p).strip() for p in partes)
    return [p for p in limpas if _com_letra(p)]


@contextmanager
def elevado(mapa: dict, nivel: str = PROTEGIDO):
    """Dentro do bloco o mapa vale, no minimo, `nivel` (o documento de menor de um processo publico e'
    tratado como protegido); na saida volta o nivel que tinha — inclusive se o bloco levantar."""
    tinha = "nivel" in mapa
    antes = mapa.get("nivel")
    mapa["nivel"] = mais_alto(do_mapa(mapa), nivel)
    try:
        yield mapa
    finally:
        if tinha:
            mapa["nivel"] = antes
        else:
            mapa.pop("nivel", None)


def _texto_da_inicial(documentos: list, textos: dict) -> str:
    partes = []
    for d in documentos:
        if d.get("tipo") in TIPOS_DA_INICIAL:
            for pagina in range(int(d["pagina_inicial"]), int(d["pagina_final"]) + 1):
                partes.append(textos.get(pagina) or "")
    return "\n".join(partes)


def _atestado_do_seletor(titulo: str) -> bool:
    """Sem seletor fora do Ulpiano: só o regex próprio da regra vale (alteração da cópia)."""
    return False


def _decidir(indice: dict, textos: dict, nomes: str, pedido: str | None) -> Nivel:
    nivel, motivos = PUBLICO, []

    def sobe(para: str, motivo: str) -> None:
        nonlocal nivel
        nivel = mais_alto(nivel, para)
        if motivo not in motivos:
            motivos.append(motivo)

    processo = indice.get("processo") or {}
    documentos = indice.get("documentos") or []
    if processo.get("indicio_sigilo"):
        sobe(SIGILOSO, M_SIGILO)
    if pedido in (PROTEGIDO, SIGILOSO):
        sobe(pedido, M_PEDIDO)
    if nomes != "regra":
        sobe(PROTEGIDO, M_SEMPRE if nomes == "sempre" else M_SEM_AVALIACAO)
    # calibracao do juiz (04/10/2026): o indice sem as partes da capa nao protege por si; o documento de menor
    # nao sobe o processo (a montagem trata so' aquele documento: documento_de_menor, rotulo_de_menor, elevado)
    if not documentos:
        sobe(PROTEGIDO, M_SEM_AVALIACAO)
        return Nivel(nivel, tuple(motivos))
    titulos = [_titulo(d) for d in documentos]
    if any(SINAIS["documento"].search(t) or _atestado_do_seletor(t) for t in titulos):
        sobe(PROTEGIDO, M_DOCUMENTO)
    inicial = _texto_da_inicial(documentos, textos or {})
    if not inicial.strip():
        sobe(PROTEGIDO, M_SEM_INICIAL)
        return Nivel(nivel, tuple(motivos))
    for rotulo, padrao in SINAIS["pedidos"].items():
        if len(padrao.findall(inicial)) >= SINAIS["minimo"]:
            sobe(PROTEGIDO, f"a inicial discute {rotulo}")
    if SINAIS["menor"].search(inicial):
        sobe(PROTEGIDO, M_MENOR)
    return Nivel(nivel, tuple(motivos))


def decidir(indice: dict, textos: dict[int, str], *, nomes: str = "regra", pedido: str | None = None) -> Nivel:
    """O nivel do processo. `textos`: {pagina: texto} do autos.sqlite (conversas.ler_textos). Qualquer falha
    da regra devolve protegido — nunca publico por engano."""
    try:
        return _decidir(indice, textos, nomes, pedido)
    except Exception:  # noqa: BLE001 — na duvida, o mais protetivo
        return Nivel(PROTEGIDO, (M_SEM_AVALIACAO,))


def ler_pedido(dossie: Path | None) -> str | None:
    """O nivel que o juiz pediu para o processo (protegido ou sigiloso); None sem pedido ou ilegivel."""
    if dossie is None:
        return None
    try:
        dados = json.loads((Path(dossie) / NOME_PEDIDO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    nivel = dados.get("nivel") if isinstance(dados, dict) else None
    return nivel if nivel in (PROTEGIDO, SIGILOSO) else None


def gravar_pedido(dossie: Path, nivel: str) -> str:
    """Grava o pedido do juiz e devolve o que ficou valendo: so' sobe (protegido sobre sigiloso mantem
    sigiloso). ValueError para o que nao e' protegido nem sigiloso."""
    if nivel not in (PROTEGIDO, SIGILOSO):
        raise ValueError("nível de proteção: só protegido ou sigiloso podem ser pedidos")
    fica = mais_alto(nivel, ler_pedido(dossie) or PUBLICO)
    Path(dossie).mkdir(parents=True, exist_ok=True)
    _gravar(Path(dossie) / NOME_PEDIDO, {"nivel": fica})
    return fica


def _gravar(caminho: Path, dados: dict) -> None:
    """Escrita atomica: o pedido truncado seria lido como "sem pedido", e o processo cairia em silencio do
    nivel pedido pelo juiz. Import tardio (a execucao nao e' da privacidade)."""
    from .mapa import escrever_atomico
    escrever_atomico(caminho, json.dumps(dados, ensure_ascii=False, indent=1))


def impressao(nomes: str, pedido: str | None, confirmados: int = 0, revisao: int = 0,
              descoberta: str | None = None) -> dict:
    """O que do nivel entra na impressao do dossie: sempre a versao dos sinais (recalibrar nivel_sinais.json
    refaz os dossies ja' montados); "nomes" e "pedido" so' fora do padrao (regra, sem pedido); "nomes_confirmados"
    (a versao do pedido de nomes do juiz, incertos.versao) so' depois do primeiro nome confirmado; "nomes_revisao"
    (incertos.revisao, toda gravacao do juiz no pedido de nomes) so' depois da primeira; "descoberta" (a versao da
    descoberta de nomes, pseudonimizador.VERSAO_DESCOBERTA_DE_NOMES) quando o chamador a passa — a etapa montar
    sempre a passa, e muda-la refaz os dossies ja' montados."""
    saida: dict = {"sinais": SINAIS["versao"]}
    if nomes != "regra" or pedido is not None:
        saida.update({"nomes": nomes, "pedido": pedido})
    if confirmados:
        saida["nomes_confirmados"] = int(confirmados)
    if revisao:
        saida["nomes_revisao"] = int(revisao)
    if descoberta:
        saida["descoberta"] = str(descoberta)
    return saida


def gravar_resultado(pasta_execucao: Path, nivel: Nivel, menor_em_documento: bool = False) -> None:
    """`menor_em_documento`: o processo e' publico e ao menos um documento de menor foi com os nomes em codigo
    (conteudo ou rotulo) — Task 11."""
    _gravar(Path(pasta_execucao) / NOME_RESULTADO, {"nome": nivel.nome, "motivos": list(nivel.motivos),
                                                    "menor_em_documento": bool(menor_em_documento)})


def ler_resultado(pasta_execucao: Path | None) -> dict | None:
    """{"nome", "motivos", "menor_em_documento"} da execucao do dossie (a ultima chave False quando ausente ou
    fora de true); None sem o arquivo, ilegivel ou com nome fora do esperado.
    O motivo desconhecido (um rotulo renomeado pela calibracao) so' sai da lista: o nivel fica — perder o
    sigiloso por um rotulo devolveria o processo ao trabalho automatico."""
    if pasta_execucao is None:
        return None
    try:
        dados = json.loads((Path(pasta_execucao) / NOME_RESULTADO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(dados, dict) or dados.get("nome") not in NIVEIS:
        return None
    brutos = dados.get("motivos")
    motivos = [m for m in brutos if isinstance(m, str) and m in MOTIVOS_POSSIVEIS] \
        if isinstance(brutos, (list, tuple)) else []
    return {"nome": dados["nome"], "motivos": motivos, "menor_em_documento": dados.get("menor_em_documento") is True}
