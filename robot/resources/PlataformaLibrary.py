"""Biblioteca de palavras-chave para o Robot Framework.

Não reimplementa nada: reusa os mesmos helpers da suite em `unittest`. A lógica
de verificação vive num lugar só; aqui ela é exposta em linguagem de negócio,
para quem lê o relatório sem ler o código.
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)

from suite import config                       # noqa: E402
from suite.base import http, propriedade, unidade_ativa   # noqa: E402
from suite.sanitize import Sanitizador         # noqa: E402

ROBOT_LIBRARY_SCOPE = "GLOBAL"
ROBOT_AUTO_KEYWORDS = True


class PlataformaLibrary:

    # ── infraestrutura ────────────────────────────────────────────────
    def os_servicos_de_apoio_devem_estar_ativos(self):
        """Nomes vem de config (genericos no repo, reais no qa.local.env)."""
        inativos = [s for s in config.SERVICES if not unidade_ativa(s)]
        if inativos:
            raise AssertionError(f"{len(inativos)} servico(s) de apoio fora do ar")
        return len(config.SERVICES)

    def deve_haver_no_maximo_uma_instancia_de_jogo(self):
        ativas = [u for u in config.GAME_UNITS if unidade_ativa(u)]
        if len(ativas) > 1:
            raise AssertionError(f"instancias simultaneas: {ativas}")
        return ativas

    def as_instancias_devem_se_excluir(self):
        a, b = config.GAME_UNITS[0], config.GAME_UNITS[1]
        if b not in propriedade(a, "Conflicts"):
            raise AssertionError(f"{a} nao declara conflito com {b}")
        if a not in propriedade(b, "Conflicts"):
            raise AssertionError(f"{b} nao declara conflito com {a}")

    def o_limite_de_memoria_deve_existir(self):
        v = propriedade(config.GAME_UNITS[0], "MemoryHigh")
        if v in ("", "infinity"):
            raise AssertionError("MemoryHigh ausente na unidade de jogo")
        return v

    # ── downloads ─────────────────────────────────────────────────────
    def a_pagina_de_downloads_deve_responder(self):
        status, _, _ = http("/")
        if status != 200:
            raise AssertionError(f"pagina respondeu {status}")

    def o_download_deve_aceitar_retomada(self, arquivo):
        status, headers, _ = http(arquivo, headers={"Range": "bytes=100-199"})
        if status != 206:
            raise AssertionError(f"sem suporte a Range: respondeu {status}")
        if headers.get("Content-Length") != "100":
            raise AssertionError(f"trecho errado: {headers.get('Content-Length')} bytes")

    def o_maior_pacote_publicado(self):
        arqs = [(f, os.path.getsize(os.path.join(config.PUBLIC_DIR, f)))
                for f in os.listdir(config.PUBLIC_DIR)
                if f.endswith((".zip", ".jar"))]
        if not arqs:
            raise AssertionError("nenhum pacote publicado")
        return max(arqs, key=lambda x: x[1])[0]

    # ── seguranca ─────────────────────────────────────────────────────
    def a_propriedade_do_servidor_deve_ser(self, chave, esperado):
        caminho = os.path.join(config.SERVER_DIR, "server.properties")
        with open(caminho) as f:
            for linha in f:
                if linha.startswith(chave + "="):
                    valor = linha.split("=", 1)[1].strip()
                    if valor != esperado:
                        raise AssertionError(f"{chave}={valor}, esperado {esperado}")
                    return valor
        raise AssertionError(f"{chave} nao encontrado")

    def o_texto_nao_pode_conter_dado_sensivel(self, texto):
        limpo = Sanitizador(config.SERVER_DIR)(texto)
        if limpo != texto:
            raise AssertionError("o texto contem dado que seria redigido")

    def o_sanitizador_deve_redigir(self, texto):
        limpo = Sanitizador(config.SERVER_DIR)(texto)
        if limpo == texto:
            raise AssertionError(f"nao redigiu: {texto!r}")
        return limpo

    # ── mundos ────────────────────────────────────────────────────────
    def os_mundos_do_disco(self):
        return sorted(d for d in os.listdir(config.SERVER_DIR)
                      if os.path.isfile(os.path.join(config.SERVER_DIR, d, "level.dat")))

    def todo_mundo_deve_ter_instrucao_de_instalacao(self):
        with open(os.path.join(config.BOT_DIR, "data", "modpacks.json")) as f:
            packs = json.load(f)
        faltando = [m for m in self.os_mundos_do_disco() if m not in packs]
        if faltando:
            raise AssertionError(f"mundos sem instrucao: {faltando}")
