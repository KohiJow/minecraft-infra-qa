"""Backups: existência, rotação, integridade e publicação.

Defeito real: o backup ia para uma nuvem que estourou a cota e falhava em
silêncio por dias. Hoje é local, publicado por HTTP e verificado aqui.
"""
import gzip
import os
import tarfile
import time

from suite import config
from suite.base import CasoBase

DIR = os.path.join(config.PUBLIC_DIR, "backups")


def _pacotes():
    try:
        return [f for f in os.listdir(DIR) if f.endswith(".tar.gz")]
    except OSError:
        return []


class TestBackups(CasoBase):
    def setUp(self):
        self.exigir_servidor()
        self.pacotes = _pacotes()
        if not self.pacotes:
            self.skipTest("nenhum backup ainda")

    def test_existe_backup_recente(self):
        """Mais de 48h sem backup é falha operacional."""
        mais_novo = max(os.path.getmtime(os.path.join(DIR, f)) for f in self.pacotes)
        idade_h = (time.time() - mais_novo) / 3600
        self.assertLess(idade_h, 48, f"backup mais novo tem {idade_h:.0f}h")

    def test_rotacao_respeitada(self):
        """Sem rotação o disco enche e o servidor para."""
        por_mundo = {}
        for f in self.pacotes:
            mundo = f.split("__")[0] if "__" in f else "?"
            por_mundo.setdefault(mundo, []).append(f)
        for mundo, arqs in por_mundo.items():
            if mundo == "config-e-contas":
                continue
            with self.subTest(mundo=mundo):
                self.assertLessEqual(len(arqs), config.BACKUP_KEEP,
                                     f"{mundo} tem {len(arqs)} backups")

    def test_arquivos_nao_estao_corrompidos(self):
        """Backup que não abre não é backup."""
        for f in sorted(self.pacotes)[-3:]:
            with self.subTest(arquivo=f):
                caminho = os.path.join(DIR, f)
                try:
                    with gzip.open(caminho, "rb") as g:
                        g.read(1 << 20)
                except OSError as e:
                    self.fail(f"gzip inválido: {e}")

    def test_backup_contem_dados_de_jogador(self):
        """Backup sem playerdata não protege o progresso de ninguém."""
        mundos = [f for f in self.pacotes if not f.startswith("config-e-contas")]
        if not mundos:
            self.skipTest("sem backup de mundo")
        alvo = max(mundos, key=lambda f: os.path.getmtime(os.path.join(DIR, f)))
        with tarfile.open(os.path.join(DIR, alvo)) as t:
            nomes = t.getnames()[:4000]
        self.assertTrue(any("/playerdata" in n for n in nomes) or
                        any("level.dat" in n for n in nomes),
                        "backup não contém dados do mundo")

    def test_indice_publicado_e_atual(self):
        indice = os.path.join(DIR, "index.html")
        self.assertTrue(os.path.exists(indice), "índice de backups não publicado")
        with open(indice) as f:
            html = f.read()
        for f_ in self.pacotes[:5]:
            with self.subTest(arquivo=f_):
                self.assertIn(f_, html, "backup não aparece no índice")
