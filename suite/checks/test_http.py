"""Servidor de downloads: é por onde os jogadores pegam os pacotes de mods.

Por que importa: pacote de 720 MB sem suporte a retomada faz quem tem internet
ruim recomeçar do zero a cada queda. Isso foi um defeito real, corrigido.
"""
import json
import os

from suite import config
from suite.base import CasoBase, http


class TestDownloads(CasoBase):
    def test_pagina_inicial_responde(self):
        self.exigir_http()
        status, _, corpo = http("/")
        self.assertEqual(status, 200)
        self.assertIn(b"<", corpo, "resposta não parece HTML")

    def test_pagina_explica_cada_mundo(self):
        """Antes era listagem crua de diretório e ninguém sabia o que baixar."""
        self.exigir_http()
        _, _, corpo = http("/")
        try:
            packs = json.load(open(f"{config.BOT_DIR}/data/modpacks.json"))
        except (OSError, ValueError):
            self.skipTest("modpacks.json indisponível")
        texto = corpo.decode("utf-8", "replace")
        self.assertGreater(len(packs), 0)
        self.assertIn("card", texto, "página não tem os blocos por mundo")

    def test_retomada_de_download(self):
        """Range/206: sem isso, queda de internet recomeça o download."""
        self.exigir_http()
        alvo = self._maior_pacote()
        if not alvo:
            self.skipTest("nenhum pacote publicado")
        status, headers, _ = http(alvo, headers={"Range": "bytes=100-199"})
        self.assertEqual(status, 206, "servidor não suporta retomada")
        self.assertIn("Content-Range", headers)
        self.assertEqual(headers.get("Content-Length"), "100")

    def test_todos_os_pacotes_publicados_baixam(self):
        self.exigir_http()
        try:
            packs = json.load(open(f"{config.BOT_DIR}/data/modpacks.json"))
        except (OSError, ValueError):
            self.skipTest("modpacks.json indisponível")
        for mundo, info in packs.items():
            link = (info or {}).get("link") or ""
            if not link.startswith("http"):
                continue
            arq = link.rsplit("/", 1)[-1]
            if not os.path.exists(os.path.join(config.PUBLIC_DIR, arq)):
                continue  # link externo
            with self.subTest(mundo=mundo):
                status, _, _ = http(arq, metodo="HEAD")
                self.assertEqual(status, 200, f"pacote de {mundo} não baixa")

    def test_indice_de_backups_publicado(self):
        self.exigir_http()
        status, _, _ = http("/backups/")
        self.assertEqual(status, 200)

    def _maior_pacote(self):
        try:
            arqs = [(f, os.path.getsize(os.path.join(config.PUBLIC_DIR, f)))
                    for f in os.listdir(config.PUBLIC_DIR)
                    if f.endswith((".zip", ".jar"))]
        except OSError:
            return None
        return max(arqs, key=lambda x: x[1])[0] if arqs else None
