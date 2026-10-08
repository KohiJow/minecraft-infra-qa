"""Bot de exemplo para o CI: estrutura correta."""
import os

TOKEN = os.environ["BOT_TOKEN"]


def command(name, **kw):
    def deco(f):
        return f
    return deco


def porta_aberta():
    return True


@command("!ping")
async def cmd_ping(message, content):
    if porta_aberta():
        await message.channel.send("pong")


if __name__ == "__main__":
    print(TOKEN)
