import base64
import json

import httpx

from app.settings import settings


async def getArticles(amount: int) -> list[tuple[str, str]]:
    result = []
    async with httpx.AsyncClient() as client:
        payload = {
            "amount": amount
        }
        response = await client.post(settings.habrApiUrl + "/articles/get/md", json=payload)

        responseJson = json.loads(response.content)

        for key in responseJson:
            decoded = base64.b64decode(responseJson[key].encode('ascii')).decode('utf-8')
            result.append((key, decoded))
    return result


async def getArticleByUrl(url: str) -> tuple[str, str]:
    result = ("", "")
    async with httpx.AsyncClient() as client:
        payload = {
            "url": url
        }
        response = await client.post(settings.habrApiUrl + "/article/get/md", json=payload)

        responseJson = json.loads(response.content)

        for key in responseJson:
            decoded = base64.b64decode(responseJson[key].encode('ascii')).decode('utf-8')
            result = (key, decoded)
    return result


async def rateArticle(username: str, url: str, rating: int) -> None:
    async with httpx.AsyncClient() as client:
        payload = {
            "username": username,
            "url": url,
            "rating": rating
        }
        response = await client.post(settings.habrApiUrl + "/article/rate", json=payload)
        if response.status_code != 200:
            raise Exception
