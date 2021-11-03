import json
from dataclasses import dataclass
from os import name
from typing import List, Tuple
from urllib.parse import urljoin

import requests
from lxml import etree

from webview_module import Response, requests_js


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
class Anime_info:
    poster: str
    title: str
    description: str
    genre: Tuple[str, ...]
    type: str
    numberOfEpisodes: int


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

    def get_anime_page(self, link) -> None:
        xpath_query = '//select[@name="series"]'
        self.response: Response = requests_js().get_html(link, xpath_query)
        self.root: etree._Element = etree.fromstring(
            self.response.document,
            etree.HTMLParser(encoding="utf-8")
        )

    def get_anime_info(self, link: str) -> Anime_info:
        self.get_anime_page(link)
        if self.root.xpath('//div[@class="player-blocked"]'):
            raise AnimeGO_Exception('Anime is bloked')
        xpath_query = '//script[@type="application/ld+json"]'
        info: dict = json.loads(self.root.xpath(xpath_query)[0].text)

        self.anime_info = Anime_info(
            title=info.get('name'),
            description=info.get('description'),
            type=info.get('@type'),
            numberOfEpisodes=len(self.root.xpath(
                '//select[@name="series"]')[0].getchildren()),
            poster=urljoin(self.domain, info.get('image')),
            genre=info.get('genre')
        )
        return self.anime_info

    def get_dubs(self, link: str, episode_num: int):
        header = {
            'Host': 'animego.org',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'X-Requested-With': 'XMLHttpRequest',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': link,
            'Cookie': 'device_view=full; censored=true',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        episode_id: str = self.root.xpath(
            '//select[@name="series"]'
        )[0].getchildren()[episode_num].get("value")

        series: dict = requests.get(
            "https://animego.org/anime/series",
            params={'id': episode_id},
            headers=header
        ).json()

        if series.get("status") == "success" and not series.get("blockEpisode"):
            content: etree._Element = etree.fromstring(
                series.get("content"),
                etree.HTMLParser(encoding="utf-8"))
            dub = content.xpath('//div[@id="video-dubbing"]/span')
            vid = content.xpath('//div[@id="video-players"]')[0]
            dubs = set(map(
                lambda x: (
                    x.xpath('span')[0].text.strip(),
                    tuple(map(
                        lambda x: x.get("data-player"),
                        vid.xpath(
                            f"""span[@data-provide-dubbing="{x.get('data-dubbing')}"]""")
                    ))
                ),
                dub))
            return tuple(map(lambda x: Dub(dubber=x[0], links=x[1]), dubs))


if __name__ == "__main__":
    ag = AnimeGo_Parser()
    anime_finds = ag.search("евангелион")
    for anime_find in anime_finds:
        print("###############")
        print(anime_find.title, "-", anime_find.link)
        print()

        try:
            anime_info = ag.get_anime_info(anime_find.link)
            print(anime_info.title)
            print(anime_info.type)
            print(anime_info.numberOfEpisodes)
            print()

            dubs = ag.get_dubs(anime_finds[1].link, 0)
            print(tuple(map(lambda x: x.dubber, dubs)))
        except Exception as e:
            if e == "Anime is bloked":
                print("Anime is bloked")
