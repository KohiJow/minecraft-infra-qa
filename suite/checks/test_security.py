"""Segurança e privacidade.

Duas frentes:
 1. O servidor em si (whitelist, autenticação, o que está exposto por HTTP).
 2. A própria suite, garantir que o relatório publicado não leva dado de
    ninguém. É o teste que torna seguro publicar isto num portfólio.
"""
import json
import os
import re

from suite import config
from suite.base import CasoBase
from suite.sanitize import Sanitizador

RAIZ_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Padrões que jamais podem aparecer em arquivo publicado
PROIBIDOS = [
    (re.compile(r"https://(?:discord|discordapp)\.com/api/webhooks/\S+"), "webhook do Discord"),
    (re.compile(r"\b[A-Za-z0-9_-]{24,28}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,}\b"), "token"),
    (re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,})\b"), "token do GitHub"),
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"), "UUID de jogador"),
    (re.compile(r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}"), "hash de senha"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "e-mail"),
]


def _publicos():
    """Arquivos que vão para o repositório."""
    saida = []
    for raiz, dirs, arqs in os.walk(RAIZ_REPO):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
        for a in arqs:
            if a.endswith((".json", ".md", ".py", ".yml", ".yaml", ".txt", ".sh")):
                saida.append(os.path.join(raiz, a))
    return saida


class TestServidor(CasoBase):
    def _propriedades(self):
        caminho = os.path.join(config.SERVER_DIR, "server.properties")
        if not os.path.exists(caminho):
            self.skipTest("server.properties indisponível")
        d = {}
        with open(caminho) as f:
            for linha in f:
                if "=" in linha and not linha.startswith("#"):
                    k, v = linha.split("=", 1)
                    d[k.strip()] = v.strip()
        return d

    def test_whitelist_ligada(self):
        """Regressão real: o jogo regerou o server.properties e voltou a
        white-list=false com o servidor já escutando na porta."""
        self.exigir_servidor()
        p = self._propriedades()
        self.assertEqual(p.get("white-list"), "true", "servidor aberto a qualquer um")

    def test_modo_offline_tem_autenticacao_compensatoria(self):
        """O grupo usa clientes não-originais, então online-mode fica false.
        Isso permite personificação, tem de haver mod de senha instalado."""
        self.exigir_servidor()
        p = self._propriedades()
        if p.get("online-mode") == "true":
            return  # autenticado pela Mojang, nada a compensar
        mods = os.path.join(config.SERVER_DIR, "mods")
        try:
            jars = os.listdir(mods)
        except OSError:
            self.skipTest("pasta de mods indisponível")
        self.assertTrue(any("login" in j.lower() or "auth" in j.lower() for j in jars),
                        "modo offline sem mod de autenticação")

    def test_pasta_publica_nao_expoe_dado_de_jogador(self):
        """Só pacote de mods e backup podem estar publicados por HTTP."""
        self.exigir_servidor()
        proibidos = {"whitelist.json", "ops.json", "server.properties",
                     "banned-players.json", "usercache.json", "players.json"}
        for raiz, _, arqs in os.walk(config.PUBLIC_DIR):
            for a in arqs:
                with self.subTest(arquivo=a):
                    self.assertNotIn(a, proibidos, f"{a} exposto por HTTP")

    def test_backup_de_mundo_nao_vai_para_nuvem_de_terceiros(self):
        self.exigir_systemd()
        alvo = next((x for x in config.SCRIPTS if "backup" in x and "index" not in x), None)
        if not alvo:
            self.skipTest("script de backup não mapeado neste ambiente")
        try:
            with open(f"/usr/local/bin/{alvo}") as f:
                s = f.read()
        except OSError:
            self.skipTest("script ausente")
        for alvo in ("rclone", "gdrive", "dropbox", "s3://"):
            with self.subTest(destino=alvo):
                self.assertNotIn(alvo, s)


class TestPrivacidadeDoRelatorio(CasoBase):
    """Estes rodam em qualquer lugar, inclusive no CI."""

    def test_sanitizador_cobre_cada_classe_de_segredo(self):
        s = Sanitizador(config.SERVER_DIR, extras=["SegredoLiteral"])
        amostras = {
            "token_github": "chave github_pat_11ABCDEFGHIJKLMNOPQRSTU_vWxYz0123456789abcdefgh",
            "ip": "conecte em 203.0.113.45 agora",
            "uuid": "jogador 06eefc19-32d5-39fc-8499-024d3bac6945",
            "email": "contato fulano.silva@exemplo.com.br",
            "webhook": "https://discord.com/api/webhooks/123/abcDEF",
            "home": "arquivo em /home/alguem/bot.py",
            "extra": "valor SegredoLiteral aqui",
        }
        for nome, texto in amostras.items():
            with self.subTest(tipo=nome):
                limpo = s(texto)
                self.assertNotEqual(limpo, texto, f"{nome} não foi redigido")
                self.assertIn("<", limpo)

    def test_versao_nao_e_confundida_com_endereco(self):
        """Regressão: a primeira versão do padrão de IP acusava "5.0.2.517",
        que é número de versão de um mod. Falso positivo numa verificação de
        segurança é tão ruim quanto o defeito: ensina a ignorar o alerta."""
        s = Sanitizador(config.SERVER_DIR)
        for versao in ("ChanceCubes-1.21.1-5.0.2.517.jar", "NeoForge 21.1.230",
                       "pacote 2.300.1.999"):
            with self.subTest(versao=versao):
                self.assertEqual(s(versao), versao, "versão redigida como endereço")

    def test_ip_publico_e_redigido(self):
        s = Sanitizador(config.SERVER_DIR)
        self.assertIn("<IP>", s("conecte em 203.0.113.45"))

    def test_ip_privado_e_preservado(self):
        """Redigir 127.0.0.1 só atrapalharia a leitura do relatório."""
        s = Sanitizador(config.SERVER_DIR)
        self.assertIn("127.0.0.1", s("servindo em 127.0.0.1:25580"))

    def test_nenhum_arquivo_do_repositorio_contem_segredo(self):
        """O teste que torna seguro publicar isto."""
        achados = []
        for caminho in _publicos():
            try:
                with open(caminho, encoding="utf-8", errors="replace") as f:
                    conteudo = f.read()
            except OSError:
                continue
            if os.path.basename(caminho) == "test_security.py":
                continue  # contém os próprios padrões
            for padrao, rotulo in PROIBIDOS:
                for m in padrao.finditer(conteudo):
                    achados.append(f"{rotulo} em {os.path.relpath(caminho, RAIZ_REPO)}")
        self.assertEqual(achados, [], f"segredo em arquivo publicado: {achados[:5]}")

    def test_relatorio_publicado_passa_pelo_sanitizador(self):
        caminho = os.path.join(RAIZ_REPO, "reports", "latest.json")
        if not os.path.exists(caminho):
            self.skipTest("ainda não há relatório")
        with open(caminho) as f:
            bruto = f.read()
        for padrao, rotulo in PROIBIDOS:
            with self.subTest(tipo=rotulo):
                self.assertIsNone(padrao.search(bruto), f"{rotulo} no relatório")
