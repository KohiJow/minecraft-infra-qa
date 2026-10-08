"""Contrato dos endpoints de catálogo e as garantias de privacidade."""
import re

# Octeto 0-255 de propósito: a versão sem validação acusava "5.0.2.517",
# que é número de versão de um mod, como se fosse endereço. Falso positivo
# pego pelo próprio teste na primeira execução.
_OCT = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
VAZAMENTOS = [
    (re.compile(rf"\b(?:{_OCT}\.){{3}}{_OCT}\b"), "endereço IP"),
    (re.compile(r"/home/|/srv/|/usr/local"), "caminho de disco"),
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"), "identificador de jogador"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "e-mail"),
]
ENDPOINTS = ["/api/status", "/api/worlds", "/api/backups"]


def test_catalogo_de_mundos(api):
    corpo = api.get("/api/worlds").json()
    assert corpo["total"] == len(corpo["mundos"])
    for m in corpo["mundos"]:
        assert m["mundo"]
        assert isinstance(m["precisa_instalar"], bool)
        if m["precisa_instalar"]:
            assert m["pacote"], f"{m['mundo']} exige instalação mas não tem pacote"


def test_pacote_anunciado_realmente_baixa(api):
    """O catálogo não pode prometer um arquivo que não existe."""
    for m in api.get("/api/worlds").json()["mundos"]:
        if m.get("pacote"):
            r = api.head("/" + m["pacote"])
            assert r.status == 200, f"pacote de {m['mundo']} não baixa"


def test_catalogo_de_backups(api):
    corpo = api.get("/api/backups").json()
    assert corpo["total"] == len(corpo["backups"])
    tempos = [b["quando"] for b in corpo["backups"]]
    assert tempos == sorted(tempos, reverse=True), "backups fora de ordem"
    for b in corpo["backups"]:
        assert b["bytes"] > 0


def test_nenhum_endpoint_vaza_dado_sensivel(api):
    """Esta porta é pública: nada de pessoal pode sair por ela."""
    for caminho in ENDPOINTS:
        texto = api.get(caminho).text()
        for padrao, rotulo in VAZAMENTOS:
            assert not padrao.search(texto), f"{rotulo} exposto em {caminho}"


def test_rota_inexistente_responde_404(api):
    assert api.get("/api/nao-existe").status == 404


def test_metodo_head_funciona(api):
    """Monitor costuma usar HEAD para não baixar o corpo."""
    assert api.head("/api/status").status == 200
