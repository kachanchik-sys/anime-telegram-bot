from time import sleep
import requests
from requests.api import head, request

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

class requests_js():
    def _back(self, window: Window, wait_xpath_query: str) -> str:
        window.evaluate_js("window.scrollTo(0, document.body.scrollHeight);")
        js_xpath_query_code = f"document.evaluate('{wait_xpath_query}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;"
        for i in range(10):
            sleep(0.3)
            if not window.evaluate_js(js_xpath_query_code) is None:
                self.page_html: str = window.evaluate_js(
                    'document.documentElement.innerHTML;')
                window.destroy()
                return self.page_html

        request_webview_exception(f"Time out waiting '{js_xpath_query_code}'")

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
            headers = resp.headers
        )
        
         


if __name__ == "__main__":
    with open("test.html", "w") as f:
        f.write(requests_js().get_html(
            'https://animego.org/anime/povelitel-m101', '//select[@name="series"]').document)
