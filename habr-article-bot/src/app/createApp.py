import asyncio

from app.telegram import start_bot


def createApp():
    asyncio.run(start_bot())
