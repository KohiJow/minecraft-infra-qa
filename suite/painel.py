#!/usr/bin/env python3
"""Gera um painel SVG com o estado da plataforma e da suite.

Pensado para ser embutido em README do GitHub: é um arquivo estático,
regerado todo dia, sem JavaScript e sem chamada externa. Funciona em tema
claro e escuro porque traz o próprio fundo.
"""
import datetime
import json
import os
import sys
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from suite import config          # noqa: E402

FUNDO, CARTAO, BORDA = "#0d1117", "#161b22", "#30363d"
TEXTO, FRACO, ACENTO = "#e6edf3", "#8b949e", "#58a6ff"
VERDE, VERMELHO, AMBAR = "#3fb950", "#f85149", "#d29922"


def _api(caminho):
    try:
        url = config.HTTP_BASE.rstrip("/") + caminho
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.load(r)
    except Exception:
        return {}


def _relatorio():
    try:
        with open(os.path.join(RAIZ, "reports", "latest.json")) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _cartao(x, y, w, h, titulo, valor, detalhe, cor):
    return f'''  <g>
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{CARTAO}" stroke="{BORDA}"/>
    <text x="{x+16}" y="{y+24}" font-size="11" fill="{FRACO}" letter-spacing="1.2">{_esc(titulo.upper())}</text>
    <text x="{x+16}" y="{y+56}" font-size="25" font-weight="600" fill="{cor}">{_esc(valor)}</text>
    <text x="{x+16}" y="{y+78}" font-size="12" fill="{FRACO}">{_esc(detalhe)}</text>
  </g>'''


def montar():
    st = _api("/api/status")
    mundos = _api("/api/worlds")
    backups = _api("/api/backups")
    rel = _relatorio()

    no_ar = bool(st.get("no_ar"))
    resumo = rel.get("resumo", {})
    passou = resumo.get("passou", 0)
    total = rel.get("total", 0)
    quebrados = resumo.get("falhou", 0) + resumo.get("erro", 0)
    saudavel = rel.get("saudavel", False)

    tam_total = sum(b.get("bytes", 0) for b in backups.get("backups", []))
    gb = tam_total / 2**30

    L = 860
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{L}" height="300" viewBox="0 0 {L} 300" role="img">',
           f'  <rect width="{L}" height="300" rx="12" fill="{FUNDO}"/>',
           f'  <text x="28" y="40" font-size="19" font-weight="700" fill="{TEXTO}" '
           f'font-family="system-ui,-apple-system,Segoe UI,sans-serif">Plataforma de servidores de jogo</text>',
           f'  <text x="28" y="62" font-size="12.5" fill="{FRACO}" '
           f'font-family="system-ui,-apple-system,Segoe UI,sans-serif">'
           f'infraestrutura monitorada por suite automatizada | relatorio diario</text>',
           f'  <circle cx="{L-40}" cy="36" r="6" fill="{VERDE if no_ar else FRACO}"/>',
           f'  <text x="{L-54}" y="41" text-anchor="end" font-size="12" fill="{FRACO}" '
           f'font-family="system-ui,sans-serif">{"no ar" if no_ar else "desligado"}</text>']

    out.append('  <g font-family="system-ui,-apple-system,Segoe UI,sans-serif">')
    larg, gap, x0, y0, alt = 192, 15, 28, 86, 96
    jog = st.get("jogadores_online")
    vagas = st.get("vagas") or 0
    out.append(_cartao(x0, y0, larg, alt, "servidor",
                       st.get("mundo") or "-",
                       f"Minecraft {st.get('versao_jogo') or '-'}",
                       VERDE if no_ar else FRACO))
    out.append(_cartao(x0 + (larg+gap), y0, larg, alt, "jogando agora",
                       f"{jog}" if jog is not None else "-",
                       f"de {vagas} vagas" if vagas else "servidor desligado",
                       VERDE if (jog or 0) > 0 else FRACO))
    out.append(_cartao(x0 + 2*(larg+gap), y0, larg, alt, "suite",
                       f"{passou}/{total}" if total else "-",
                       "nenhuma falha" if saudavel else f"{quebrados} com falha",
                       VERDE if saudavel else VERMELHO))
    out.append(_cartao(x0 + 3*(larg+gap), y0, larg, alt, "mundos",
                       str(mundos.get("total", 0)),
                       f"{backups.get('total',0)} backups, {gb:.1f} GB", ACENTO))

    # faixa com os mundos
    y = y0 + alt + 22
    out.append(f'  <text x="{x0}" y="{y}" font-size="11" fill="{FRACO}" letter-spacing="1.2">MUNDOS DISPONIVEIS</text>')
    cx = x0
    for m in mundos.get("mundos", [])[:6]:
        nome = _esc(m.get("mundo", "?"))
        precisa = m.get("precisa_instalar")
        w = max(74, 11 + len(nome) * 7.6 + 12)
        cor = AMBAR if precisa else VERDE
        out.append(f'    <rect x="{cx}" y="{y+12}" width="{w:.0f}" height="26" rx="13" '
                   f'fill="{CARTAO}" stroke="{cor}" stroke-opacity="0.5"/>')
        out.append(f'    <circle cx="{cx+13}" cy="{y+25}" r="3.5" fill="{cor}"/>')
        out.append(f'    <text x="{cx+23}" y="{y+29}" font-size="12" fill="{TEXTO}">{nome}</text>')
        cx += w + 9
    out.append(f'  <text x="{x0}" y="{y+60}" font-size="11" fill="{FRACO}">'
               f'verde = entra sem instalar nada | ambar = precisa do pacote de mods</text>')

    carimbo = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    out.append(f'  <text x="{L-28}" y="{y+60}" text-anchor="end" font-size="11" fill="{FRACO}">'
               f'atualizado em {carimbo}</text>')
    out.append('  </g>')
    out.append('</svg>')
    return "\n".join(out)


if __name__ == "__main__":
    destino = os.path.join(RAIZ, "reports", "painel.svg")
    svg = montar()
    with open(destino, "w") as f:
        f.write(svg)
    print(f"painel gerado: {len(svg)} bytes")
