"""Infraestrutura: serviços, exclusão mútua e scripts de operação.

Por que importa: o servidor roda duas instâncias de Minecraft que compartilham
a MESMA porta. Se as duas subirem juntas, uma falha e os jogadores caem.
"""
import os

from suite import config
from suite.base import CasoBase, propriedade, unidade_ativa




class TestServicos(CasoBase):
    def test_servicos_de_apoio_ativos(self):
        """Bot e servidor de downloads precisam estar sempre no ar."""
        self.exigir_systemd()
        for s in config.SERVICES:
            with self.subTest(servico=s):
                self.assertTrue(unidade_ativa(s), f"{s} não está ativo")

    def test_exatamente_uma_instancia_de_jogo(self):
        """As duas instâncias dividem a porta: nunca podem rodar juntas."""
        self.exigir_systemd()
        ativas = [u for u in config.GAME_UNITS if unidade_ativa(u)]
        self.assertLessEqual(len(ativas), 1,
                             f"mais de uma instância no ar: {ativas}")

    def test_exclusao_mutua_declarada_nos_dois_sentidos(self):
        """Conflicts= precisa existir dos dois lados; só um lado não protege."""
        self.exigir_systemd()
        a, b = config.GAME_UNITS[0], config.GAME_UNITS[1]
        self.assertIn(b, propriedade(a, "Conflicts"), f"{a} não declara conflito com {b}")
        self.assertIn(a, propriedade(b, "Conflicts"), f"{b} não declara conflito com {a}")

    def test_limite_de_memoria_preservado(self):
        """Regressão real: apagar um drop-in removeu o MemoryHigh sem aviso."""
        self.exigir_systemd()
        valor = propriedade(config.GAME_UNITS[0], "MemoryHigh")
        self.assertNotIn(valor, ("", "infinity"), "MemoryHigh sumiu da unidade")

    def test_timer_de_backup_armado(self):
        self.exigir_systemd()
        self.assertTrue(unidade_ativa(config.TIMER), f"{config.TIMER} não está armado")

    def test_scripts_de_operacao_executaveis(self):
        self.exigir_systemd()
        if not config.SCRIPTS:
            self.skipTest("QA_SCRIPTS não definido neste ambiente")
        for s in config.SCRIPTS:
            with self.subTest(script=s):
                caminho = f"/usr/local/bin/{s}"
                self.assertTrue(os.path.isfile(caminho), f"{s} não existe")
                self.assertTrue(os.access(caminho, os.X_OK), f"{s} não é executável")

    def test_backup_nao_depende_mais_de_nuvem_externa(self):
        """O backup ia para um Drive que estourou a cota e falhava calado."""
        self.exigir_systemd()
        alvo = next((s for s in config.SCRIPTS if "backup" in s and "index" not in s), None)
        if not alvo:
            self.skipTest("script de backup não mapeado neste ambiente")
        try:
            with open(f"/usr/local/bin/{alvo}") as f:
                conteudo = f.read()
        except OSError:
            self.skipTest("script ausente")
        self.assertNotIn("rclone", conteudo, "backup voltou a depender de nuvem externa")
