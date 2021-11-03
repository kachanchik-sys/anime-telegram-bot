from dataclasses import dataclass
from os import name
from typing import List, Tuple
import json
from urllib.parse import urljoin

import requests
from lxml import etree
import json

from requests.api import request

from modules.webview_module import Response, requests_js

class AnimeGO_Exception(Exception):
    pass


@dataclass
class Anime_finds:
    link: str
    poster: str
    title: str

@dataclass
class Dub:
    dubber: str
    links: Tuple[str, ...]


@dataclass
class Anime:
    poster: str
    title: str
    description: str
    genre: Tuple[str,...]
    type: str
    numberOfEpisodes: int
    dubs: Tuple[Dub, ...]


class AnimeGo_Parser():
    def __init__(self) -> None:
        self.domain = "https://animego.org"
        self._link = "https://animego.org/search/anime"
        stat_code = requests.head(self._link).status_code
        if not requests.head(self._link).status_code == 200:
            raise AnimeGO_Exception(
                f"status code not equal to 200 ({stat_code})")

    def search(self, query: str) -> Tuple[Anime_finds, ...]:
        response = requests.get(self._link, params={"q": query})

        root = etree.fromstring(
            response.text,
            etree.HTMLParser(encoding="utf-8")
        )

        anime_links: Tuple[str, ...] = tuple(map(
            lambda x: x.get("href"),
            root.xpath("//div[@class='card border-0']/div[1]/a[1]")
        ))
        anime_posters: Tuple[str, ...] = tuple(map(
            lambda x: x.get("data-original"),
            root.xpath("//div[@class='card border-0']/div[1]/a[1]/div[1]")
        ))
        anime_titels_eng: Tuple[str, ...] = tuple(map(
            lambda x: x.text,
            root.xpath("//div[@class='card border-0']/div[2]/div[1]/div[1]")
        ))

        return [(lambda i: Anime_finds(anime_links[i], anime_posters[i], anime_titels_eng[i]))(i) for i in range(len(anime_links))]

    
    def get_anime_info(self, link: str) -> Anime:
        xpath_query = '//script[@type="application/ld+json"]'
        response:Response = requests_js().get_html(link, xpath_query)
        root: etree._Element = etree.fromstring(
            response.document,
            etree.HTMLParser(encoding="utf-8")
        )
        info:dict = json.loads(root.xpath(xpath_query)[0].text)

        anime_info = Anime(
            title = info.get('name'),
            description = info.get('description'),
            type = info.get('@type'),
            episods = info.get('numberOfEpisodes'),
            poster = urljoin(self.domain, info.get('image'))
        )


if __name__ == "__main__":
    ag = AnimeGo_Parser()
    anime = ag.search("Владыка")
    ag.get_anime_info(anime[1].link)

