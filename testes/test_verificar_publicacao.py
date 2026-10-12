# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Conferência pré-publicação: varredura do histórico, e-mails dos commits, dist/."""
import _base  # noqa: F401
import hashlib
import tempfile
from pathlib import Path

from empacotamento import verificar_publicacao as V

EMAIL_PESSOAL = "alguem@" + "provedor-qualquer" + ".net"          # montado em partes: nunca aparece pronto no repositório
CAMINHO_MAQUINA = "\\".join(("C:", "Users", "fulano"))
GITHUB = "1+a@" + "users.noreply.github.com"            # idem: a guarda só conhece os domínios de exemplo


def test_email_permitido_so_os_dominios_de_placeholder_e_do_github():
    assert V.email_permitido(GITHUB)
    assert V.email_permitido("noreply@anthropic.com") and V.email_permitido("contato@exemplo.com.br")
    assert V.email_permitido("a@example.com") and V.email_permitido("x@sub.exemplo.com.br")
    assert not V.email_permitido(EMAIL_PESSOAL)
    assert not V.email_permitido("a@" + "meuexample.com") and not V.email_permitido("a@" + "anthropic.com.evil.net")
    assert not V.email_permitido("a@" + "exemplo.org") and not V.email_permitido("a@" + "xusers.noreply.github.com")


def test_varrer_acha_email_caminho_e_termos_mascarados_sem_repetir():
    texto = ("commit abcdef1234567890\ndiff --git a/dir/arq.txt b/dir/arq.txt\n"
             f"+Author: Fulano <{EMAIL_PESSOAL}>\n+caminho {CAMINHO_MAQUINA}\\x.txt\n"
             f"+de novo {CAMINHO_MAQUINA}\\y.txt\n+ok contato@exemplo.com.br e C:\\Users\\<usuário>\\z\n"
             "+relato: BELTRANO qualquer\n+/home/<usuário>/a e /c/Users/<nome>/b\n")
    achados = V.varrer(texto, ["Beltrano Qualquer", "Sicrano"])
    assert any(a.endswith("e-mail a***@p***.net") for a in achados), achados
    assert any(a.endswith("caminho " + CAMINHO_MAQUINA[:-6] + "f***") for a in achados), achados
    assert any(a.endswith("termo B***************r") for a in achados), achados
    assert all(a.startswith("abcdef1 dir/arq.txt: ") for a in achados), achados
    assert len(achados) == 3, achados                               # o caminho repetido conta uma vez; placeholders não contam
    brutos = (EMAIL_PESSOAL, "fulano", "eltrano", "icrano")
    assert not any(b.lower() in a.lower() for a in achados for b in brutos), achados   # nunca o valor cru
    assert V.varrer("+nada aqui\n", []) == []


def test_varrer_caminhos_de_outros_formatos():
    achados = V.varrer("+/home/" + "joao/x e /c/Users/" + "maria/y\n", [])
    assert any(a.endswith("caminho /" + "home/j***") for a in achados), achados
    assert any(a.endswith("caminho /c/" + "Users/m***") for a in achados), achados
    assert V.varrer("+/home/" + "j***/x e /c/Users/" + "m***/y" + chr(10), []) == []   # máscara não é nome


def test_fonte_do_proprio_regex_nao_e_caminho_mas_usuario_com_letra_e():
    fonte = "(?<![" + chr(92) + "w.:-])/" + "home/)(?!<)([^" + chr(92) + chr(92) + "/])"
    assert V.varrer("+" + fonte + chr(10), []) == []
    assert V.varrer("+/home/" + "jo/x" + chr(10), []) != []


def test_termos_ausentes_usa_so_os_padroes_embutidos():
    with tempfile.TemporaryDirectory() as d:
        assert V.carregar_termos(Path(d) / "nao-existe.txt") == []
        arq = Path(d) / "termos.txt"
        arq.write_text("# comentário\nBeltrano Qualquer\n\n  Sicrano  \n", encoding="utf-8")
        assert V.carregar_termos(arq) == ["Beltrano Qualquer", "Sicrano"]
    assert V.varrer(f"+{EMAIL_PESSOAL}\n", []) == ["texto: e-mail a***@p***.net"]


def test_emails_dos_commits_todos_do_github():
    ok = f"abc1234 {GITHUB} {GITHUB}\n"
    assert V.emails_fora_do_github(ok) == []
    ruim = ok + f"def5678 {EMAIL_PESSOAL} {GITHUB}\n"
    assert V.emails_fora_do_github(ruim) == ["def5678: a***@p***.net"]


def test_emails_dos_commits_linha_curta_ou_saida_vazia_e_pendencia():
    assert V.emails_fora_do_github("")
    r = V.emails_fora_do_github(f"abc1234 {GITHUB}\n")
    assert len(r) == 1 and r[0].startswith("abc1234:")


def test_conferir_dist_exige_setup_e_sha256sums_batendo():
    with tempfile.TemporaryDirectory() as d:
        dist = Path(d)
        assert any("Pseudonimizador-Setup.exe" in p for p in V.conferir_dist(dist))
        setup = dist / "Pseudonimizador-Setup.exe"
        setup.write_bytes(b"MZ setup")
        assert any("SHA256SUMS.txt" in p for p in V.conferir_dist(dist))
        (dist / "SHA256SUMS.txt").write_text("0" * 64 + "  Pseudonimizador-Setup.exe\n", encoding="utf-8")
        assert any("não bate" in p for p in V.conferir_dist(dist))
        (dist / "SHA256SUMS.txt").write_text(f"{hashlib.sha256(b'MZ setup').hexdigest()}  Pseudonimizador-Setup.exe\n",
                                             encoding="utf-8")
        assert V.conferir_dist(dist) == []


class R:
    def __init__(self, rc, out=""):
        self.returncode, self.stdout, self.stderr = rc, out, ""


def _dist_ok(d):
    dist = Path(d) / "dist"
    dist.mkdir()
    (dist / "Pseudonimizador-Setup.exe").write_bytes(b"MZ")
    (dist / "SHA256SUMS.txt").write_text(f"{hashlib.sha256(b'MZ').hexdigest()}  Pseudonimizador-Setup.exe\n",
                                         encoding="utf-8")
    return dist


def _executar_limpo(log="+tudo limpo\n"):
    def executar(args, **kw):
        if "--format=%h %ae %ce" in args:
            return R(0, f"abc1234 {GITHUB} {GITHUB}\n")
        return R(0, log)
    return executar


def test_main_com_comandos_falsos_lista_as_pendencias_e_sai_1():
    with tempfile.TemporaryDirectory() as d:
        dist = Path(d) / "dist"
        dist.mkdir()
        chamadas = []

        def executar(args, **kw):
            chamadas.append(list(args))
            if "--format=%h %ae %ce" in args:
                return R(0, f"abc1234 {GITHUB} {GITHUB}\n")
            if "-p" in args:
                return R(0, f"+texto com {CAMINHO_MAQUINA}\n")
            return R(0)
        rc = V.main(["--dist", str(dist), "--termos", str(Path(d) / "nao-existe.txt")], executar=executar)
    assert rc == 1
    assert any("executar_todos.py" in " ".join(c) for c in chamadas)
    assert any("test_sem_dados_reais.py" in " ".join(c) for c in chamadas)
    assert any(c[:3] == ["git", "log", "--all"] and "-m" in c for c in chamadas)


def test_main_tudo_limpo_sai_0():
    with tempfile.TemporaryDirectory() as d:
        dist = _dist_ok(d)
        termos = Path(d) / "t.txt"
        termos.write_text("Beltrano Qualquer\n", encoding="utf-8")
        assert V.main(["--dist", str(dist), "--termos", str(termos), "--sem-suite"], executar=_executar_limpo()) == 0


def test_main_sem_lista_de_termos_e_pendencia_salvo_sem_termos():
    with tempfile.TemporaryDirectory() as d:
        dist = _dist_ok(d)
        base = ["--dist", str(dist), "--termos", str(Path(d) / "x.txt"), "--sem-suite"]
        assert V.main(base, executar=_executar_limpo()) == 1
        assert V.main(base + ["--sem-termos"], executar=_executar_limpo()) == 0


def test_main_termo_no_historico_sai_1():
    with tempfile.TemporaryDirectory() as d:
        dist = _dist_ok(d)
        termos = Path(d) / "t.txt"
        termos.write_text("Beltrano Qualquer\n", encoding="utf-8")
        rc = V.main(["--dist", str(dist), "--termos", str(termos), "--sem-suite"],
                    executar=_executar_limpo("+fala do BELTRANO qualquer\n"))
    assert rc == 1


def test_main_git_log_falho_ou_git_ausente_e_pendencia():
    with tempfile.TemporaryDirectory() as d:
        dist = _dist_ok(d)
        base = ["--dist", str(dist), "--termos", str(Path(d) / "x.txt"), "--sem-suite", "--sem-termos"]

        def falha(args, **kw):
            return R(128) if args[0] == "git" else R(0)
        assert V.main(base, executar=falha) == 1

        def ausente(args, **kw):
            if args[0] == "git":
                raise FileNotFoundError("git")
            return R(0)
        assert V.main(base, executar=ausente) == 1


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
