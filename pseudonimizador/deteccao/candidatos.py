# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Candidatos a nome de pessoa e de empresa num documento avulso (sem capa do
PJe): âncoras de qualificação de contrato, a qualificação depois do nome, o
léxico de prenomes e sobrenomes do motor e os sufixos societários. Tudo é
sugestão: a revisão humana decide (spec §6). A caixa não decide nada."""
from __future__ import annotations

import re

from ..motor.lexico import SOBRENOMES, frequencia_de_sobrenome
from ..motor.mapa import normalizar
from ..motor.pseudonimizador import CONECTIVOS, RE_SUFIXO_PJ, _NUNCA_NOME, _prenome_provado

# inicial seguida de ponto ("S.", "C.") conta como palavra do nome, se vem outra palavra depois
RE_INICIAL = re.compile(r"[^\W\d_]\.")
RE_PALAVRA = re.compile(r"[^\W\d_]\.(?=[ 	 ][^\W\d_])|[^\W\d_]+(?:['’\-][^\W\d_]+)*")
RE_SO_ESPACO = re.compile(r"[ \t\u00a0]{1,3}")
# UMA quebra de linha (com espa\u00e7os em volta): o nome que termina no fim de uma
# linha e continua na seguinte, quando a primeira palavra dela \u00e9 sobrenome
RE_QUEBRA = re.compile(r"[ \t\u00a0]*\r?\n[ \t\u00a0]*")

RE_ANCORA = re.compile(
    r"(?i)\b(?:contratante|contratad[ao]|locador[a]?|locat[áa]ri[ao]|outorgante|outorgad[ao]|"
    r"comprador[a]?|vendedor[a]?|promitentes?\s+(?:comprador|vendedor)[a]?|fiador[a]?|cedente|"
    r"cession[áa]ri[ao]|empregador[a]?|empregad[ao]|testemunhas?|titular(?:es)?(?:\s+da\s+conta)?|representante\s+legal|s[óo]ci[ao]|"
    r"procurador[a]?|interveniente|devedor[a]?|credor[a]?)\s*(?:\d+\s*)?[:\-–—]\s*"
    r"|(?i:\brepresentad[ao]\s+(?:neste\s+ato\s+)?por\s+)"
    r"|(?i:\b(?:raz[ãa]o\s+social|denominad[ao])\s*:?\s+)")
RE_QUALIFICACAO = re.compile(
    r"(?i),\s*(?:brasileir[oa]|estrangeir[oa]|nacionalidade|portador[a]?|inscrit[oa]|CPF|CNPJ|RG|"
    r"estado\s+civil|solteir[oa]|casad[oa]|divorciad[oa]|vi[úu]v[oa]|maior|menor)\b")
# ME/EPP/SLU só valem como sufixo pela posição: antes de pontuação, fim de linha ou CNPJ/"inscrita"
# (senão o pronome "me" viraria sufixo)
RE_SUFIXO = re.compile(
    r"(?<!\w)(?:ltda\.?|s\.\s?a\.?|s/a|eireli"
    r"|(?:epp|ME|SLU)(?=\s*(?:[,;.:)\n]|$)|\s+(?:CNPJ|inscrit)))(?!\w)", re.I)
RE_SUFIXO_ADIANTE = re.compile(r"\s*" + RE_SUFIXO.pattern, re.I)
_LIGACAO = CONECTIVOS - {"e"}  # dentro de um nome só "da/de/do/das/dos" continuam; "e" encerra
_SUFIXO_EXIGE_DUAS = {"me", "epp", "slu"}

_PARADAS = {"brasileiro", "brasileira", "estrangeiro", "estrangeira", "portador", "portadora",
            "inscrito", "inscrita", "residente", "domiciliado", "domiciliada", "casado", "casada",
            "solteiro", "solteira", "nacionalidade", "neste", "ato", "doravante", "pessoa", "empresa",
            "sociedade", "com", "sede", "cpf", "cnpj", "rg", "denominado", "denominada", "representado",
            "representada", "que", "para", "por", "pelo", "pela", "o", "a", "os", "as", "sr", "sra",
            "senhor", "senhora", "entre", "em", "no", "na", "ao", "firma", "razao", "social"}
MAX_PALAVRAS = 8


def _sobrenome(n: str) -> bool:
    return (n in SOBRENOMES or frequencia_de_sobrenome(n) > 0) and n not in _NUNCA_NOME and n not in CONECTIVOS


def _significativas(nome: str) -> int:
    return sum(1 for w in nome.split() if normalizar(w) not in CONECTIVOS)


def _ler_adiante(s: str, pos: int) -> tuple[int, int] | None:
    """Palavras a partir de `pos`, separadas por espaço simples, até pontuação,
    quebra de linha ou palavra de parada. Tira conectivos do fim."""
    palavras = []
    i = pos
    quebrou = False
    while len(palavras) < MAX_PALAVRAS:
        m = RE_PALAVRA.match(s, i)
        if not m or normalizar(m.group()) in _PARADAS:
            break
        palavras.append(m)
        prox = RE_SO_ESPACO.match(s, m.end())
        if not prox:
            # nome que acaba no fim da linha e segue na próxima, uma única vez
            quebra = RE_QUEBRA.match(s, m.end())
            seg = RE_PALAVRA.match(s, quebra.end()) if quebra and not quebrou else None
            if not seg or normalizar(seg.group()) in _PARADAS or not _sobrenome(normalizar(seg.group())):
                break
            quebrou = True
            i = quebra.end()
            continue
        i = prox.end()
    while palavras and normalizar(palavras[-1].group()) in CONECTIVOS:
        palavras.pop()
    if not palavras:
        return None
    ini, fim = palavras[0].start(), palavras[-1].end()
    # sufixo societário logo depois ("... Tecidos Ltda.") faz parte do nome
    suf = RE_SUFIXO_ADIANTE.match(s, fim)
    if suf:
        fim = suf.end()
    return (ini, fim) if _significativas(s[ini:fim]) >= 2 else None


def _ler_atras(s: str, pos: int) -> tuple[int, int] | None:
    """Palavras imediatamente antes de `pos`, de trás para a frente, até
    pontuação ou palavra de parada. Tira conectivos do começo."""
    palavras = [m for m in RE_PALAVRA.finditer(s, max(0, pos - 200), pos)]
    escolhidas = []
    fim_esperado = pos
    for m in reversed(palavras):
        if not RE_SO_ESPACO.fullmatch(s[m.end():fim_esperado]) and m.end() != fim_esperado:
            break
        if normalizar(m.group()) in _PARADAS or len(escolhidas) >= MAX_PALAVRAS:
            break
        escolhidas.insert(0, m)
        fim_esperado = m.start()
    while escolhidas and normalizar(escolhidas[0].group()) in CONECTIVOS:
        escolhidas.pop(0)
    if not escolhidas:
        return None
    ini, fim = escolhidas[0].start(), escolhidas[-1].end()
    return (ini, fim) if _significativas(s[ini:fim]) >= 2 else None


def _categoria(nome: str, contexto: str = "") -> str:
    return "empresa" if RE_SUFIXO_PJ.search(nome) or RE_SUFIXO.search(nome) or "cnpj" in contexto.lower() \
        else "pessoa"


def _por_ancora(s: str) -> list[tuple[int, int, str]]:
    achados = []
    for m in RE_ANCORA.finditer(s):
        span = _ler_adiante(s, m.end())
        if span:
            achados.append((*span, _categoria(s[span[0]:span[1]])))
    return achados


def _por_qualificacao(s: str) -> list[tuple[int, int, str]]:
    achados = []
    for m in RE_QUALIFICACAO.finditer(s):
        fim_nome = m.start()
        # "Ltda., inscrita": o sufixo com ponto antes da vírgula
        suf = None
        for sm in RE_SUFIXO.finditer(s, max(0, fim_nome - 8), fim_nome):
            if sm.end() == fim_nome:
                suf = sm
        span = _ler_atras(s, suf.start() if suf else fim_nome)
        if span:
            fim = suf.end() if suf else span[1]
            achados.append((span[0], fim, _categoria(s[span[0]:fim], m.group())))
    return achados


def _por_lexico(s: str) -> list[tuple[int, int, str]]:
    palavras = list(RE_PALAVRA.finditer(s))
    achados = []
    i = 0
    while i < len(palavras):
        if not _prenome_provado(palavras[i].group()):
            i += 1
            continue
        j, ultimo, tem_sobrenome, quebrou = i, None, False, False
        while j + 1 < len(palavras):
            lacuna = s[palavras[j].end():palavras[j + 1].start()]
            w = palavras[j + 1].group()
            n = normalizar(w)
            if not RE_SO_ESPACO.fullmatch(lacuna):
                # nome que acaba no fim da linha e segue na próxima, uma única vez
                if ultimo is not None and not quebrou and RE_QUEBRA.fullmatch(lacuna) and _sobrenome(n):
                    j += 1
                    ultimo = j
                    tem_sobrenome = quebrou = True
                    continue
                break
            if n in _LIGACAO or RE_INICIAL.fullmatch(w):
                j += 1
                continue
            if _sobrenome(n) or _prenome_provado(w):
                j += 1
                ultimo = j
                tem_sobrenome = tem_sobrenome or _sobrenome(n)
                continue
            break
        if ultimo is not None and tem_sobrenome:
            achados.append((palavras[i].start(), palavras[ultimo].end(), "pessoa"))
            i = ultimo + 1
        else:
            i += 1
    return achados


def _por_sufixo(s: str) -> list[tuple[int, int, str]]:
    achados = []
    for m in RE_SUFIXO.finditer(s):
        span = _ler_atras(s, m.start())
        if not span:
            continue
        if normalizar(m.group()).strip(".") in _SUFIXO_EXIGE_DUAS and _significativas(s[span[0]:span[1]]) < 2:
            continue
        achados.append((span[0], m.end(), "empresa"))
    return achados


# palavras de rótulo que antecedem o nome sem fazer parte dele (além das âncoras)
_ROTULOS = {"assinado", "assinada", "assinatura", "nome", "cliente", "clientes", "sr", "sra", "dr", "dra",
            "senhor", "senhora", "doutor", "doutora", "parte", "partes", "autor", "autora", "requerente",
            "requerido", "requerida", "advogado", "advogada", "perito", "perita", "signatario", "signataria",
            "firmado", "firmada", "declarante", "representante", "promitente", "razao", "social", "aluno",
            "paciente", "usuario", "usuaria", "responsavel", "beneficiario", "beneficiaria", "favorecido",
            "favorecida", "sacado", "sacada", "emitente", "avalista", "conjuge", "pai", "mae", "filho", "filha"}
_FIM_DE_NOME = ",;:)("  # o que pode vir logo depois do nome, além de fim de texto e de linha
RE_PALAVRA_ANTES = re.compile(r"([^\W\d_]+)[ \t ]$")


_ROTULOS_DE_DOCUMENTO = {"cpf", "cnpj", "rg"}


def _termina_em_rotulo_de_documento(texto: str) -> bool:
    m = list(RE_PALAVRA.finditer(texto))
    return bool(m) and m[-1].end() == len(texto) and normalizar(m[-1].group()) in _ROTULOS_DE_DOCUMENTO


def _comeca_em_rotulo_de_documento(texto: str) -> bool:
    m = RE_PALAVRA.match(texto)
    return bool(m) and normalizar(m.group()) in _ROTULOS_DE_DOCUMENTO


def _prenome_solto_antes(s: str, ini: int, fim: int) -> int:
    """Início do nome estendido por UMA palavra colada antes dele, quando ela
    parece prenome fora do léxico: só letras, 3 ou mais, em forma de título, no
    começo da linha ou depois de `:;,(`, que não seja parada, conectivo,
    rótulo nem âncora, e o nome acaba em fim de linha ou pontuação (o começo de
    uma frase, como "Assinaram João Silva e ...", não entra). A maiúscula só
    desempata uma palavra já colada a um nome detectado; nunca cria nome."""
    m = RE_PALAVRA_ANTES.search(s, max(0, ini - 40), ini)
    if not m:
        return ini
    w = m.group(1)
    n = normalizar(w)
    if len(w) < 3 or not (w[0].isupper() and w[1:].islower()):
        return ini
    if n in _PARADAS or n in CONECTIVOS or n in _NUNCA_NOME or n in _ROTULOS or RE_ANCORA.match(w + ":"):
        return ini
    antes = s[max(0, m.start() - 20):m.start()].rstrip(" \t ")
    # "CPF" no fim da linha de cima chega colado (linhas do mesmo bloco do PDF se juntam com espaço)
    if antes and antes[-1] not in "\n" + ":;,(" and not _termina_em_rotulo_de_documento(antes):
        return ini
    resto = s[fim:fim + 20].lstrip(" \t ")
    if resto and resto[0] != "\n" and resto[0] not in _FIM_DE_NOME and not _comeca_em_rotulo_de_documento(resto):
        return ini
    return m.start(1)


def pessoas_e_empresas(limpo: str) -> list[tuple[int, int, str]]:
    todos = _por_ancora(limpo) + _por_qualificacao(limpo) + _por_sufixo(limpo) + _por_lexico(limpo)
    todos = [(_prenome_solto_antes(limpo, a, b) if cat == "pessoa" else a, b, cat) for a, b, cat in todos]
    # o mais longo primeiro; empresa vence pessoa no mesmo trecho
    todos.sort(key=lambda a: (a[0], -(a[1] - a[0]), a[2] != "empresa"))
    escolhidos: list[tuple[int, int, str]] = []
    for a in todos:
        if all(a[1] <= b[0] or a[0] >= b[1] for b in escolhidos):
            escolhidos.append(a)
    return sorted(escolhidos)
