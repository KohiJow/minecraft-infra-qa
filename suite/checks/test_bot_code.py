"""Análise estática do bot de operação.

Os dois defeitos abaixo passaram por testes que importavam o módulo e só
apareceram em produção. Viraram teste permanente.
"""
import ast
import os

from suite import config
from suite.base import CasoBase


def _arvore():
    caminho = os.path.join(config.BOT_DIR, "bot.py")
    with open(caminho) as f:
        return ast.parse(f.read()), f


class TestCodigoDoBot(CasoBase):
    def setUp(self):
        self.exigir_servidor()
        caminho = os.path.join(config.BOT_DIR, "bot.py")
        if not os.path.exists(caminho):
            self.skipTest("bot.py indisponível")
        with open(caminho) as f:
            self.fonte = f.read()
        self.arvore = ast.parse(self.fonte)
        blocos = [n for n in self.arvore.body
                  if isinstance(n, ast.If) and "main" in ast.dump(n.test)]
        self.main = blocos[0] if blocos else None

    def test_nada_definido_depois_do_entrypoint(self):
        """DEFEITO REAL: comandos escritos depois de client.run() nunca
        registram em produção, mas registram sob `import`, o teste passava
        e o usuário via o comando não fazer nada."""
        if self.main is None:
            self.skipTest("sem bloco __main__")
        orfas = [getattr(n, "name", type(n).__name__)
                 for n in self.arvore.body if n.lineno > self.main.lineno]
        self.assertEqual(orfas, [], f"código inalcançável em produção: {orfas}")

    def test_comandos_registram_em_producao(self):
        if self.main is None:
            self.skipTest("sem bloco __main__")
        cmds = [n for n in self.arvore.body
                if any(isinstance(d, ast.Call) and getattr(d.func, "id", "") == "command"
                       for d in getattr(n, "decorator_list", []))]
        self.assertGreater(len(cmds), 0)
        for c in cmds:
            with self.subTest(comando=c.name):
                self.assertLess(c.lineno, self.main.lineno)

    def test_sem_await_em_funcao_sincrona(self):
        """DEFEITO REAL: `await` numa função que devolve bool quebrava o
        comando com TypeError na cara do usuário."""
        sincronas = {n.name for n in ast.walk(self.arvore)
                     if isinstance(n, ast.FunctionDef)}
        assincronas = {n.name for n in ast.walk(self.arvore)
                       if isinstance(n, ast.AsyncFunctionDef)}
        so_sincronas = sincronas - assincronas
        ruins = []
        for n in ast.walk(self.arvore):
            if isinstance(n, ast.Await) and isinstance(n.value, ast.Call):
                f = n.value.func
                nome = getattr(f, "id", None) or getattr(f, "attr", None)
                if nome in so_sincronas:
                    ruins.append((n.lineno, nome))
        self.assertEqual(ruins, [], f"await em função síncrona: {ruins}")

    def test_sem_segredo_escrito_no_codigo(self):
        """Token tem de vir do ambiente, não do arquivo."""
        self.assertNotIn("DISCORD_TOKEN = \"", self.fonte)
        self.assertIn("os.environ", self.fonte)

    def test_codigo_compila(self):
        compile(self.fonte, "bot.py", "exec")
