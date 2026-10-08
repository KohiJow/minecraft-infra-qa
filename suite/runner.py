#!/usr/bin/env python3
"""Executa a suite e publica um relatório que pode ir para um repositório
público: tudo que sai daqui passa pelo sanitizador.

Saídas:
  reports/latest.json          resultado da última execução
  reports/latest.md            o mesmo, legível
  reports/badge.json           endpoint para o selo do README
  reports/history/<data>.json  histórico diário
"""
import argparse
import datetime
import io
import json
import os
import socket
import sys
import time
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from suite import config          # noqa: E402
from suite.sanitize import Sanitizador   # noqa: E402


class Coletor(unittest.TextTestResult):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.registros = []
        self._t0 = None

    def startTest(self, test):
        self._t0 = time.monotonic()
        super().startTest(test)

    def _guardar(self, test, estado, detalhe=""):
        modulo = test.__class__.__module__.rsplit(".", 1)[-1]
        self.registros.append({
            "modulo": modulo,
            "classe": test.__class__.__name__,
            "teste": test._testMethodName,
            "descricao": (test.shortDescription() or "").strip(),
            "estado": estado,
            "ms": round((time.monotonic() - (self._t0 or time.monotonic())) * 1000, 1),
            "detalhe": detalhe,
        })

    def addSuccess(self, test):
        super().addSuccess(test); self._guardar(test, "passou")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._guardar(test, "falhou", self._resumo(err))

    def addError(self, test, err):
        super().addError(test, err)
        self._guardar(test, "erro", self._resumo(err))

    def addSkip(self, test, motivo):
        super().addSkip(test, motivo); self._guardar(test, "pulado", motivo)

    @staticmethod
    def _resumo(err):
        return f"{err[0].__name__}: {err[1]}".replace("\n", " ")[:400]


def executar():
    carregador = unittest.TestLoader()
    suite = carregador.discover(os.path.join(RAIZ, "suite", "checks"), top_level_dir=RAIZ)
    fluxo = io.StringIO()
    runner = unittest.TextTestRunner(stream=fluxo, verbosity=0, resultclass=Coletor)
    inicio = time.time()
    resultado = runner.run(suite)
    return resultado, round(time.time() - inicio, 2)


def montar_relatorio(resultado, segundos, san):
    regs = [san.estrutura(r) for r in resultado.registros]
    por_estado = {}
    for r in regs:
        por_estado[r["estado"]] = por_estado.get(r["estado"], 0) + 1
    modulos = {}
    for r in regs:
        m = modulos.setdefault(r["modulo"], {"passou": 0, "falhou": 0, "erro": 0, "pulado": 0})
        m[r["estado"]] = m.get(r["estado"], 0) + 1
    quebrados = por_estado.get("falhou", 0) + por_estado.get("erro", 0)
    return {
        "gerado_em": datetime.datetime.now().replace(microsecond=0).isoformat(),
        "duracao_s": segundos,
        "host": "servidor-de-jogos",          # nunca o hostname real
        "total": len(regs),
        "resumo": por_estado,
        "saudavel": quebrados == 0,
        "por_modulo": modulos,
        "testes": regs,
    }


def markdown(rel):
    icone = {"passou": "✅", "falhou": "❌", "erro": "💥", "pulado": "⏭️"}
    L = ["# Relatório da suite", "",
         f"**{'Saudável' if rel['saudavel'] else 'Com falhas'}**. "
         f"{rel['total']} verificações em {rel['duracao_s']}s, em {rel['gerado_em']}.", "",
         "| Módulo | ✅ | ❌ | 💥 | ⏭️ |", "|---|--:|--:|--:|--:|"]
    for m, c in sorted(rel["por_modulo"].items()):
        L.append(f"| `{m}` | {c.get('passou',0)} | {c.get('falhou',0)} "
                 f"| {c.get('erro',0)} | {c.get('pulado',0)} |")
    ruins = [t for t in rel["testes"] if t["estado"] in ("falhou", "erro")]
    if ruins:
        L += ["", "## Falhas", ""]
        for t in ruins:
            L.append(f"- {icone[t['estado']]} **{t['modulo']}.{t['teste']}**, {t['detalhe']}")
    L += ["", "## Todas as verificações", "",
          "| | Verificação | O que garante | ms |", "|---|---|---|--:|"]
    for t in rel["testes"]:
        L.append(f"| {icone[t['estado']]} | `{t['modulo']}.{t['teste']}` "
                 f"| {t['descricao'] or '-'} | {t['ms']:.0f} |")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-publicar", action="store_true",
                    help="roda e imprime, sem gravar relatório")
    args = ap.parse_args()

    resultado, segundos = executar()
    san = Sanitizador(config.SERVER_DIR, extras=[socket.gethostname()])
    rel = montar_relatorio(resultado, segundos, san)

    print(f"{rel['total']} verificações | {rel['resumo']} | {segundos}s")
    if args.sem_publicar:
        return 0 if rel["saudavel"] else 1

    saida = os.path.join(RAIZ, "reports")
    os.makedirs(os.path.join(saida, "history"), exist_ok=True)
    with open(os.path.join(saida, "latest.json"), "w") as f:
        json.dump(rel, f, indent=2, ensure_ascii=False)
    with open(os.path.join(saida, "latest.md"), "w") as f:
        f.write(markdown(rel))
    dia = datetime.date.today().isoformat()
    with open(os.path.join(saida, "history", f"{dia}.json"), "w") as f:
        json.dump({k: v for k, v in rel.items() if k != "testes"}, f, indent=2, ensure_ascii=False)
    try:
        from suite import painel
        with open(os.path.join(saida, "painel.svg"), "w") as f:
            f.write(painel.montar())
    except Exception as e:
        print(f"painel nao gerado: {e}")

    quebrados = rel["resumo"].get("falhou", 0) + rel["resumo"].get("erro", 0)
    with open(os.path.join(saida, "badge.json"), "w") as f:
        json.dump({"schemaVersion": 1, "label": "suite",
                   "message": f"{rel['resumo'].get('passou',0)}/{rel['total']} passando",
                   "color": "brightgreen" if quebrados == 0 else "red"}, f)
    return 0 if rel["saudavel"] else 1


if __name__ == "__main__":
    sys.exit(main())
