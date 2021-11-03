from time import sleep
import requests
from requests.api import head, request
import logging

import webview
from webview.window import Window
from dataclasses import dataclass


class request_webview_exception(Exception):
    pass

@dataclass
class Response:
    document: str
    status_code: int
    url: str
    headers: dict
    is_fully_loaded: bool

class requests_js():
    def _back(self, window: Window, wait_xpath_query: str) -> str:
        window.evaluate_js("window.scrollTo(0, document.body.scrollHeight);")
        js_xpath_query_code = f"document.evaluate('{wait_xpath_query}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;"
        for i in range(10):
            sleep(0.3)
            if not window.evaluate_js(js_xpath_query_code) is None:
                self.is_fully_loaded = True
                break

        self.page_html: str = window.evaluate_js(
            'document.documentElement.innerHTML;')
        window.destroy()
        if i >= 9:
            logging.warn("Page was no fully loaded")
            self.is_fully_loaded = False
        return self.page_html
        
        

    def get_html(self, link: str, wait_xpath_query: str) -> Response:
        """Get html from web page with render javascript. 
        Html will only be returned if it contains an element matching the xpath query

        Args:
            link (str): link to curent website
            wait_xpath_query (str): xpath query

        Returns:
            Response : object 
        """
        resp = requests.head(link)
        if resp.status_code == 200:
            window = webview.create_window(link, link, hidden=True)
            webview.start(  # block thread until complite
                gui="gtk",
                func=self._back,
                args=(window, wait_xpath_query)
            )
            document = self.page_html
        else:
            document = requests.get(link).text
        
        return Response(
            document = document,
            status_code = resp.status_code,
            url = link,
            headers = resp.headers,
            is_fully_loaded = self.is_fully_loaded
        )
        
         


if __name__ == "__main__":
    with open("test.html", "w") as f:
        f.write(requests_js().get_html(
            'https://animego.org/anime/povelitel-m101', '//select[@name="series"]').document)
