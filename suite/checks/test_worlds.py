"""Consistência de configuração entre mundos.

A plataforma tem vários mundos, cada um com seu conjunto de mods e seus
ajustes. Três arquivos JSON precisam concordar entre si e com o disco,
um deles desalinhado faz o mundo subir com o conjunto errado.
"""
import json
import os

from suite import config
from suite.base import CasoBase


def _mundos(raiz):
    try:
        return sorted(d for d in os.listdir(raiz)
                      if os.path.isfile(os.path.join(raiz, d, "level.dat")))
    except OSError:
        return []


class TestMundos(CasoBase):
    def setUp(self):
        self.exigir_servidor()
        self.mundos = _mundos(config.SERVER_DIR)
        if not self.mundos:
            self.skipTest("nenhum mundo encontrado")
        self.mods = self._json(f"{config.SERVER_DIR}/world_mods.json")
        self.ajustes = self._json(f"{config.SERVER_DIR}/world_settings.json")
        self.packs = self._json(f"{config.BOT_DIR}/data/modpacks.json")

    def _json(self, c):
        try:
            with open(c) as f:
                return json.load(f)
        except (OSError, ValueError):
            self.skipTest(f"{os.path.basename(c)} indisponível")

    def test_todo_mundo_tem_conjunto_de_mods_mapeado(self):
        for m in self.mundos:
            with self.subTest(mundo=m):
                self.assertIn(m, self.mods, f"{m} sem conjunto de mods")

    def test_conjunto_mapeado_existe_no_disco(self):
        for m, conj in self.mods.items():
            with self.subTest(mundo=m):
                caminho = os.path.join(config.SERVER_DIR, "mods_sets", conj)
                self.assertTrue(os.path.isdir(caminho), f"conjunto '{conj}' não existe")

    def test_todo_mundo_tem_ajustes_proprios(self):
        """difficulty/pvp são globais no server.properties: sem ajuste por
        mundo, o pacote de um vaza para o outro."""
        for m in self.mundos:
            with self.subTest(mundo=m):
                self.assertIn(m, self.ajustes, f"{m} sem ajustes")

    def test_nenhuma_configuracao_aponta_para_mundo_inexistente(self):
        for nome, cfg in (("world_mods", self.mods), ("world_settings", self.ajustes)):
            for chave in cfg:
                with self.subTest(arquivo=nome, chave=chave):
                    self.assertIn(chave, self.mundos, f"{chave} não existe no disco")

    def test_todo_mundo_tem_instrucao_de_instalacao(self):
        """O jogador precisa saber o que baixar para cada mundo."""
        for m in self.mundos:
            with self.subTest(mundo=m):
                self.assertIn(m, self.packs, f"{m} sem instruções")
                info = self.packs[m] or {}
                self.assertIn("nota", info)
                if info.get("obrigatorio"):
                    self.assertTrue(info.get("link"), f"{m} exige mods mas não tem link")

    def test_molde_existe_para_mundo_resetavel(self):
        """Mundos de partida precisam poder voltar ao estado inicial."""
        moldes = set(os.listdir(os.path.join(config.SERVER_DIR, "moldes"))) \
            if os.path.isdir(os.path.join(config.SERVER_DIR, "moldes")) else set()
        for m in moldes:
            with self.subTest(molde=m):
                self.assertIn(m, self.mundos, f"molde órfão: {m}")
