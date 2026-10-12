# SPDX-License-Identifier: AGPL-3.0-only
# Termo adicional (AGPL-3.0, seção 7(b)): preservar os avisos de autoria; ver CREDITOS.md.
"""Gera empacotamento/pseudonimizador.ico (16, 32, 48 e 256 px): um quadrado
azul-escuro arredondado com duas tarjas brancas — o dado coberto. Uso:
    .venv\\Scripts\\python -X utf8 empacotamento/gerar_icone.py"""
from __future__ import annotations

import sys
from pathlib import Path

DESTINO = Path(__file__).resolve().parent / "pseudonimizador.ico"
AZUL = (31, 58, 95, 255)


def desenhar(tamanho: int):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, tamanho - 1, tamanho - 1), radius=tamanho // 5, fill=AZUL)
    m, alt = tamanho // 5, max(2, tamanho // 9)
    d.rounded_rectangle((m, tamanho * 0.36, tamanho - m, tamanho * 0.36 + alt), radius=alt // 2, fill="white")
    d.rounded_rectangle((m, tamanho * 0.58, tamanho * 0.62, tamanho * 0.58 + alt), radius=alt // 2, fill="white")
    return img


def main() -> int:
    desenhar(256).save(DESTINO, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    print(f"ícone: {DESTINO} ({DESTINO.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
