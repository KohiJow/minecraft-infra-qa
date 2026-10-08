"""Testes da própria suite.

Um teste que nunca falhou não provou nada. Aqui as verificações estruturais são
apontadas para um bot propositalmente defeituoso, que reproduz os incidentes 2
e 3, e exigimos que elas **falhem**. Se um dia pararem de falhar, a suite
perdeu o poder de detectar e eu quero saber disso no mesmo dia.
"""
import ast
import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFEITUOSO = os.path.join(RAIZ, "fixtures", "bot-defeituoso", "bot.py")
BOM = os.path.join(RAIZ, "fixtures", "bot", "bot.py")


def _arvore(caminho):
    with open(caminho) as f:
        return ast.parse(f.read())


def _orfas(arvore):
    blocos = [n for n in arvore.body if isinstance(n, ast.If) and "main" in ast.dump(n.test)]
    if not blocos:
        return []
    return [getattr(n, "name", type(n).__name__)
            for n in arvore.body if n.lineno > blocos[0].lineno]


def _await_em_sincrona(arvore):
    sincronas = {n.name for n in ast.walk(arvore) if isinstance(n, ast.FunctionDef)}
    assincronas = {n.name for n in ast.walk(arvore) if isinstance(n, ast.AsyncFunctionDef)}
    so_sincronas = sincronas - assincronas
    ruins = []
    for n in ast.walk(arvore):
        if isinstance(n, ast.Await) and isinstance(n.value, ast.Call):
            f = n.value.func
            nome = getattr(f, "id", None) or getattr(f, "attr", None)
            if nome in so_sincronas:
                ruins.append(nome)
    return ruins


class TestASuitePega(unittest.TestCase):
    """Validação negativa: a regra tem de acusar o defeito conhecido."""

    def test_acusa_codigo_depois_do_entrypoint(self):
        """Incidente 2: comando definido após o entrypoint."""
        self.assertTrue(os.path.exists(DEFEITUOSO), "fixture defeituosa ausente")
        self.assertNotEqual(_orfas(_arvore(DEFEITUOSO)), [],
                            "a regra deixou de detectar código inalcançável")

    def test_acusa_await_em_funcao_sincrona(self):
        """Incidente 3: await sobre função que devolve bool."""
        self.assertNotEqual(_await_em_sincrona(_arvore(DEFEITUOSO)), [],
                            "a regra deixou de detectar await indevido")


class TestASuiteNaoAcusaAToa(unittest.TestCase):
    """Validação positiva: nenhum falso positivo no código correto."""

    def test_codigo_correto_passa_limpo(self):
        arvore = _arvore(BOM)
        self.assertEqual(_orfas(arvore), [])
        self.assertEqual(_await_em_sincrona(arvore), [])
