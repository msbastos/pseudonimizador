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


def test_varrer_acha_email_caminho_e_termos_sem_repetir():
    texto = (f"+Author: Fulano <{EMAIL_PESSOAL}>\n+caminho {CAMINHO_MAQUINA}\\x.txt\n"
             f"+de novo {CAMINHO_MAQUINA}\\y.txt\n+ok contato@exemplo.com.br e C:\\Users\\<usuário>\\z\n"
             "+relato: Beltrano Qualquer\n")
    achados = V.varrer(texto, ["Beltrano Qualquer", "Sicrano"])
    assert f"e-mail: {EMAIL_PESSOAL}" in achados and f"caminho: {CAMINHO_MAQUINA}" in achados
    assert "termo: Beltrano Qualquer" in achados and not any("Sicrano" in a for a in achados)
    assert len(achados) == 3, achados                               # o caminho repetido conta uma vez; <usuário> não conta
    assert V.varrer("+nada aqui\n", []) == []


def test_termos_ausentes_usa_so_os_padroes_embutidos():
    with tempfile.TemporaryDirectory() as d:
        assert V.carregar_termos(Path(d) / "nao-existe.txt") == []
        arq = Path(d) / "termos.txt"
        arq.write_text("# comentário\nBeltrano Qualquer\n\n  Sicrano  \n", encoding="utf-8")
        assert V.carregar_termos(arq) == ["Beltrano Qualquer", "Sicrano"]
    assert V.varrer(f"+{EMAIL_PESSOAL}\n", []) == [f"e-mail: {EMAIL_PESSOAL}"]


def test_emails_dos_commits_todos_do_github():
    ok = f"abc1234 {GITHUB} {GITHUB}\n"
    assert V.emails_fora_do_github(ok) == []
    ruim = ok + f"def5678 {EMAIL_PESSOAL} {GITHUB}\n"
    assert V.emails_fora_do_github(ruim) == [f"def5678: {EMAIL_PESSOAL}"]


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


def test_main_com_comandos_falsos_lista_as_pendencias_e_sai_1():
    class R:
        def __init__(self, rc, out=""):
            self.returncode, self.stdout, self.stderr = rc, out, ""
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
    assert any(c[:3] == ["git", "log", "--all"] for c in chamadas)


def test_main_tudo_limpo_sai_0():
    class R:
        def __init__(self, rc, out=""):
            self.returncode, self.stdout, self.stderr = rc, out, ""
    with tempfile.TemporaryDirectory() as d:
        dist = Path(d) / "dist"
        dist.mkdir()
        (dist / "Pseudonimizador-Setup.exe").write_bytes(b"MZ")
        (dist / "SHA256SUMS.txt").write_text(f"{hashlib.sha256(b'MZ').hexdigest()}  Pseudonimizador-Setup.exe\n",
                                             encoding="utf-8")

        def executar(args, **kw):
            if "--format=%h %ae %ce" in args:
                return R(0, f"abc1234 {GITHUB} {GITHUB}\n")
            return R(0, "+tudo limpo\n")
        assert V.main(["--dist", str(dist), "--termos", str(Path(d) / "x.txt"), "--sem-suite"], executar=executar) == 0


if __name__ == "__main__":
    from _runner import rodar
    rodar(globals())
