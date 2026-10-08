"""Bot com os dois defeitos reais, usado para testar a suite."""
import os

TOKEN = os.environ["BOT_TOKEN"]


def command(name, **kw):
    def deco(f):
        return f
    return deco


def porta_aberta():
    return True


if __name__ == "__main__":
    print(TOKEN)


@command("!tarde")
async def cmd_tarde(message, content):
    await porta_aberta()
