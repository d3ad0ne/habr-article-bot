import re

from app.consts import FIND_HEADING_REGEXP, MAX_MESSAGE_LENGTH


def getArticleID(url: str) -> str:
    url = url.removesuffix("/")
    return url[url.rfind("/")+1:]


def getHeading(text: str) -> str:
    match = re.search(FIND_HEADING_REGEXP, text, re.MULTILINE)

    if match is None:
        return "Heading not found"
    else:
        return match.group(1)


def splitArticle(text: str) -> list[str]:
    parts = []
    for i in range(0, len(text), MAX_MESSAGE_LENGTH):
        parts.append(text[i:i + MAX_MESSAGE_LENGTH])
    return parts
