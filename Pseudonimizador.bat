@echo off
rem Abre a janela do Pseudonimizador sem console. Requer o ambiente .venv (README, "Instalacao").
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Ambiente nao encontrado. Siga a secao "Instalacao" do README.md.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" -X utf8 -m pseudonimizador
