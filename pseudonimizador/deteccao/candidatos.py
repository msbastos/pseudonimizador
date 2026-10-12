# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Candidatos a nome de pessoa e de empresa num documento avulso (sem capa do
PJe): âncoras de qualificação de contrato, a qualificação depois do nome, o
léxico de prenomes e sobrenomes do motor e os sufixos societários. Tudo é
sugestão: a revisão humana decide (spec §6). A caixa não decide nada."""
from __future__ import annotations

import re

from ..motor.lexico import SOBRENOMES, frequencia_de_prenome, frequencia_de_sobrenome
from ..motor.mapa import normalizar
from ..motor.pseudonimizador import (CONECTIVOS, PARADA_FORTE, RE_SUFIXO_PJ, TODA_A_LINGUA, _ENDERECO_NO_CANDIDATO,
                                     _NUNCA_NOME, _NUNCA_PRENOME_ISOLADO, _PULAVEIS_ANTES_DO_NOME, _parada,
                                     _prenome_provado)

# inicial seguida de ponto ("S.", "C.") conta como palavra do nome, se vem outra palavra depois
RE_INICIAL = re.compile(r"[^\W\d_]\.")
RE_PALAVRA = re.compile(r"[^\W\d_]\.(?=[ 	 ][^\W\d_])|[^\W\d_]+(?:['’\-][^\W\d_]+)*")
RE_SO_ESPACO = re.compile(r"[ \t\u00a0]{1,3}")
# UMA quebra de linha (com espaços em volta): o nome que termina no fim de uma
# linha e continua na seguinte, quando a primeira palavra dela é sobrenome
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


# o que a linha de baixo traz que não é nome: logradouro, bairro e afins (a palavra serve de sobrenome:
# "Rua", "Vila", "Estrada"), por isso o nome nunca continua nela
_LUGARES = _ENDERECO_NO_CANDIDATO | {"vila", "jardim", "cidade", "largo", "praca", "bairro", "setor", "sitio",
                                     "chacara", "conjunto", "parque", "distrito", "loteamento"}


def _so_sobrenome(w: str) -> bool:
    """Palavra que continua um nome na linha de baixo: sobrenome e não (só) prenome. "Fernandes" e "Silva" valem
    (muito mais sobrenome que prenome); "Carlos" e "Ana" não (outro nome da lista); "Rua" e "Vila" nunca."""
    n = normalizar(w)
    if n in _LUGARES or not _sobrenome(n):
        return False
    return not _prenome_provado(w) or frequencia_de_sobrenome(n) > frequencia_de_prenome(n)


def _continua_apos_quebra(w: str) -> bool:
    """Depois da quebra só continuam sobrenomes (e a ligação "da/de/do")."""
    return normalizar(w) in _LIGACAO or _so_sobrenome(w)


def _significativas(nome: str) -> int:
    return sum(1 for w in nome.split() if normalizar(w) not in CONECTIVOS)


def _ler_adiante(s: str, pos: int, entre_linhas: bool = True) -> tuple[int, int] | None:
    """Palavras a partir de `pos`, separadas por espaço simples, até pontuação,
    quebra de linha ou palavra de parada. Tira conectivos do fim. Com
    `entre_linhas`, UMA quebra de linha não encerra o nome se a palavra de
    baixo é sobrenome (o nome que vira a página de um PDF)."""
    palavras = []
    i = pos
    quebrou = False
    while len(palavras) < MAX_PALAVRAS:
        m = RE_PALAVRA.match(s, i)
        if not m or normalizar(m.group()) in _PARADAS or (quebrou and not _continua_apos_quebra(m.group())):
            break
        palavras.append(m)
        quebra = RE_QUEBRA.match(s, m.end()) if entre_linhas and not quebrou else None
        if quebra:
            seg = RE_PALAVRA.match(s, quebra.end())
            if not seg or normalizar(seg.group()) in _PARADAS or not _so_sobrenome(seg.group()):
                break
            quebrou = True
            i = quebra.end()
            continue
        prox = RE_SO_ESPACO.match(s, m.end())
        if not prox:
            break
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


def _ler_atras(s: str, pos: int, entre_linhas: bool = False) -> tuple[int, int] | None:
    """Palavras imediatamente antes de `pos`, de trás para a frente, até
    pontuação ou palavra de parada. Tira conectivos do começo. Com
    `entre_linhas`, atravessa UMA quebra de linha se tudo o que já está
    escolhido, depois dela, é sobrenome."""
    palavras = [m for m in RE_PALAVRA.finditer(s, max(0, pos - 200), pos)]
    escolhidas = []
    fim_esperado = pos
    quebrou = False
    for m in reversed(palavras):
        lacuna = s[m.end():fim_esperado]
        if not RE_SO_ESPACO.fullmatch(lacuna) and m.end() != fim_esperado:
            if not (entre_linhas and not quebrou and escolhidas and RE_QUEBRA.fullmatch(lacuna)
                    and all(_continua_apos_quebra(x.group()) for x in escolhidas)):
                break
            quebrou = True
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


def _por_ancora(s: str, entre_linhas: bool = True) -> list[tuple[int, int, str]]:
    achados = []
    for m in RE_ANCORA.finditer(s):
        span = _ler_adiante(s, m.end(), entre_linhas)
        if span:
            achados.append((*span, _categoria(s[span[0]:span[1]])))
    return achados


def _por_qualificacao(s: str, entre_linhas: bool = True) -> list[tuple[int, int, str]]:
    achados = []
    for m in RE_QUALIFICACAO.finditer(s):
        fim_nome = m.start()
        # "Ltda., inscrita": o sufixo com ponto antes da vírgula
        suf = None
        for sm in RE_SUFIXO.finditer(s, max(0, fim_nome - 8), fim_nome):
            if sm.end() == fim_nome:
                suf = sm
        span = _ler_atras(s, suf.start() if suf else fim_nome, entre_linhas)
        if span:
            fim = suf.end() if suf else span[1]
            achados.append((span[0], fim, _categoria(s[span[0]:fim], m.group())))
    return achados


def _por_lexico(s: str, entre_linhas: bool = True) -> list[tuple[int, int, str]]:
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
                # nome que acaba no fim da linha e segue na próxima, uma única vez (só sobrenome)
                if entre_linhas and not quebrou and RE_QUEBRA.fullmatch(lacuna) and _so_sobrenome(w):
                    j += 1
                    ultimo = j
                    tem_sobrenome = quebrou = True
                    continue
                break
            if quebrou:
                if n in _LIGACAO:
                    j += 1
                    continue
                if _so_sobrenome(w):
                    j += 1
                    ultimo = j
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


# palavras de rótulo, de papel, de parentesco e de lugar que antecedem o nome sem fazer parte dele
# (além das âncoras, de _PULAVEIS_ANTES_DO_NOME e de _NUNCA_PRENOME_ISOLADO do motor)
_ROTULOS = {"assinado", "assinada", "assinatura", "nome", "cliente", "clientes", "sr", "sra", "dr", "dra",
            "senhor", "senhora", "doutor", "doutora", "parte", "partes", "autor", "autora", "requerente",
            "requerido", "requerida", "advogado", "advogada", "perito", "perita", "signatario", "signataria",
            "firmado", "firmada", "declarante", "representante", "promitente", "razao", "social", "aluno",
            "paciente", "usuario", "usuaria", "responsavel", "beneficiario", "beneficiaria", "favorecido",
            "favorecida", "sacado", "sacada", "emitente", "avalista", "conjuge", "pai", "mae", "filho", "filha",
            "denominada", "denominado", "representada", "representado", "exequente", "executado", "executada",
            "executados", "relator", "relatora", "prezado", "prezada", "presidente", "escola", "hospital",
            "edificio", "fazenda", "vila", "colegio", "instituto", "universidade", "faculdade", "clinica",
            "sogro", "sogra", "tio", "tia", "avo", "neto", "neta", "irmao", "irma", "esposo", "esposa", "marido",
            "assinou", "atenciosamente", "cordialmente", "respeitosamente", "viuvo", "viuva", "herdeiro", "herdeira",
            "inventariante", "juiz", "juiza", "promovente", "promovido", "promovida", "impetrante", "impetrado",
            "tabelia", "tabeliao", "oficiala", "oficial", "escrivao", "escriva", "professora", "professor",
            "corretor", "corretora", "interessada", "interessado", "curador", "curadora", "ass"}
# o que a palavra do papel, do fecho ou do verbo costuma terminar ("Presidente", "Atenciosamente", "Assinou",
# "Assinaram", "Considerando", "Declaração", "Comunidade"); "-ia", "-ada" e "-al" ficam de fora (Zuleia, Zuleida)
_FINS_DE_PALAVRA_COMUM = ("mente", "ante", "ente", "ou", "aram", "ndo", "ção", "dade")
_FIM_DE_NOME = ",;:).("  # o que pode vir logo depois do nome, além de fim de texto, de linha e de " - "
_TRACOS = "-–—"
RE_PALAVRA_ANTES = re.compile("([^\\W\\d_]+)[ \\t\u00a0]{1,3}$")
RE_MARCADOR_DE_LISTA = re.compile(r"(?:^|\n)[ \t]*(?:\d{1,3}[.)]|[•*])$")
RE_ANCORA_COM_NUMERO = re.compile(r"([^\W\d_]+)\s*\d+$")
_ROTULOS_DE_DOCUMENTO = {"cpf", "cnpj", "rg"}


def _termina_em_rotulo_de_documento(texto: str) -> bool:
    m = list(RE_PALAVRA.finditer(texto))
    return bool(m) and m[-1].end() == len(texto) and normalizar(m[-1].group()) in _ROTULOS_DE_DOCUMENTO


def _comeca_em_rotulo_de_documento(texto: str) -> bool:
    m = RE_PALAVRA.match(texto)
    return bool(m) and normalizar(m.group()) in _ROTULOS_DE_DOCUMENTO


def _palavra_da_lingua_ou_de_papel(w: str) -> bool:
    n = normalizar(w)
    return (n in _PARADAS or n in _LUGARES or n in CONECTIVOS or n in _NUNCA_NOME or n in _ROTULOS or n in _NUNCA_PRENOME_ISOLADO
            or n in _PULAVEIS_ANTES_DO_NOME or RE_ANCORA.match(w + ":") is not None
            or w.lower().endswith(_FINS_DE_PALAVRA_COMUM)
            or _parada(n, 0, frozenset(), TODA_A_LINGUA) == PARADA_FORTE)


def _antes_aceita(a: str) -> bool:
    """O que vem antes da palavra (sem os espaços do fim): começo do texto ou da linha, pontuação de abertura,
    traço ou linha de assinatura, marcador de lista, âncora com número ("Testemunha 2") ou rótulo de documento."""
    if not a or a[-1] in "\n:;,(_" + _TRACOS:
        return True
    if RE_MARCADOR_DE_LISTA.search(a) or _termina_em_rotulo_de_documento(a):
        return True
    m = RE_ANCORA_COM_NUMERO.search(a)
    return bool(m) and RE_ANCORA.match(m.group(1) + ":") is not None


def _depois_aceito(resto: str) -> bool:
    """O que vem depois do nome (sem os espaços do começo): fim do texto ou da linha, pontuação, traço ou rótulo."""
    return not resto or resto[0] == "\n" or resto[0] in _FIM_DE_NOME + _TRACOS or _comeca_em_rotulo_de_documento(resto)


def _prenome_solto_antes(s: str, ini: int, fim: int) -> int:
    """Início do nome estendido por UMA palavra colada antes dele, quando ela
    parece prenome fora do léxico: só letras, 3 ou mais, em forma de título,
    que não seja palavra da língua (a do motor: parada, papel, parentesco,
    lugar, fecho, verbo), conectivo, rótulo nem âncora, depois de um começo de
    linha ou de pontuação (ver _antes_aceita), e o nome acaba em fim de linha,
    pontuação ou rótulo (_depois_aceito). A maiúscula só desempata uma palavra
    já colada a um nome detectado; nunca cria nome."""
    m = RE_PALAVRA_ANTES.search(s, max(0, ini - 40), ini)
    if not m:
        return ini
    w = m.group(1)
    if len(w) < 3 or not (w[0].isupper() and w[1:].islower()) or _palavra_da_lingua_ou_de_papel(w):
        return ini
    if not _antes_aceita(s[max(0, m.start() - 30):m.start()].rstrip(" \t\u00a0")):
        return ini
    if not _depois_aceito(s[fim:fim + 20].lstrip(" \t\u00a0")):
        return ini
    return m.start(1)


def pessoas_e_empresas(limpo: str, entre_linhas: bool = True) -> list[tuple[int, int, str]]:
    todos = (_por_ancora(limpo, entre_linhas) + _por_qualificacao(limpo, entre_linhas) + _por_sufixo(limpo)
             + _por_lexico(limpo, entre_linhas))
    todos = [(_prenome_solto_antes(limpo, a, b) if cat == "pessoa" else a, b, cat) for a, b, cat in todos]
    # o mais longo primeiro; empresa vence pessoa no mesmo trecho
    todos.sort(key=lambda a: (a[0], -(a[1] - a[0]), a[2] != "empresa"))
    escolhidos: list[tuple[int, int, str]] = []
    for a in todos:
        if all(a[1] <= b[0] or a[0] >= b[1] for b in escolhidos):
            escolhidos.append(a)
    return sorted(escolhidos)
