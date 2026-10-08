"""Contrato do endpoint de status.

É o que um painel externo ou um monitor consome. Quebrar o contrato quebra
quem depende dele, então cada campo é verificado por presença e por tipo.
"""
import time

CAMPOS = {
    "no_ar": bool,
    "jogadores_online": (int, type(None)),
    "instancia": (str, type(None)),
    "versao_jogo": (str, type(None)),
    "mundo": (str, type(None)),
    "vagas": int,
    "consultado_em": int,
}


def test_responde_200_e_json(api):
    r = api.get("/api/status")
    assert r.status == 200
    assert "application/json" in r.headers.get("content-type", "")


def test_contrato_de_campos(api):
    corpo = api.get("/api/status").json()
    for campo, tipo in CAMPOS.items():
        assert campo in corpo, f"campo ausente: {campo}"
        assert isinstance(corpo[campo], tipo), f"{campo} com tipo errado"


def test_coerencia_entre_campos(api):
    """Se está no ar, precisa dizer qual instância e qual mundo."""
    corpo = api.get("/api/status").json()
    if corpo["no_ar"]:
        assert corpo["instancia"], "no ar mas sem instância"
        assert corpo["mundo"], "no ar mas sem mundo"
        assert corpo["vagas"] > 0, "no ar mas sem vagas"
    else:
        assert corpo["instancia"] is None


def test_contagem_de_jogadores_faz_sentido(api):
    """O número vem do protocolo do jogo, em tempo real. Não pode passar das
    vagas nem ser negativo, e com o servidor desligado tem de ser nulo."""
    corpo = api.get("/api/status").json()
    jog = corpo["jogadores_online"]
    if corpo["no_ar"]:
        assert jog is not None, "no ar mas sem contagem de jogadores"
        assert 0 <= jog <= corpo["vagas"], f"contagem fora da faixa: {jog}/{corpo['vagas']}"
    else:
        assert jog is None


def test_horario_e_recente(api):
    corpo = api.get("/api/status").json()
    assert abs(time.time() - corpo["consultado_em"]) < 120


def test_nao_e_cacheado(api):
    """Status cacheado mente. O cabeçalho precisa impedir isso."""
    r = api.get("/api/status")
    assert "no-store" in r.headers.get("cache-control", "")
