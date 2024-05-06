# fetch list, http, socks4, sock5
# iterate over and test each
import requests
import typing
import logging
import json
from pathlib import Path


class Basket:

    request_headers: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Accept": "*/*",
    }
    proxy_sources: dict[str, str] = {
        "SpeedX": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master"
    }

    request_timeout: int = 3

    thread_amount:int = 5

    indent_level: int = 3

    proxy_dir = Path(__file__).parents[1] / "files"

    path_to_proxies: dict[str, Path] = {
        "http": proxy_dir / "http.json",
        "socks4": proxy_dir / "sock4.json",
        "socks5": proxy_dir / "socks5.json",
    }

    test_resource_url: str = (
        "https://raw.githubusercontent.com/Simatwa/free-proxies/master/files/test.md"
    )

    @classmethod
    def fetch(cls, url: str, **kwargs) -> requests.Response:
        """ "Make Get request

        Args:
            url (str): Path to resource.
            kwargs : Request parameters.

        Returns:
            httpx.Response: response
        """
        response = requests.get(url,headers=Basket.request_headers, **kwargs)
        response.raise_for_status()
        return response

    @classmethod
    def check_status(
        cls, proxy: str, type: typing.Literal["http", "socks4", "socks5"]
    ) -> bool:
        """Test working status of proxy

        Args:
            proxy (str): host:port
            type (typing.Literal["http", "socks4", "socks5"]):

        Returns:
            bool: is proxy working?
        """
        proxy_in_dict = {
            "https": f"{type}://{proxy}"
            }
        try:
            resp = cls.fetch(
                Basket.test_resource_url, proxies=proxy_in_dict
            )
            resp.raise_for_status()
            assert resp.ok, f"{proxy} not working"
            logging.info(f"{resp.status_code}, {resp.reason} : ({type}, {proxy})")
            return True
        except Exception as e:
            logging.error(
                f'[{proxy_in_dict['https']}] {e.args[1] if e.args and len(e.args)>1 else e}'
            )
            return False

    @classmethod
    def save_proxy(
        cls,
        identity: str,
        proxy: list[str],
    ):
        """Dump working proxy to path

        Args:
            identity (str): Name
            proxy (list[str]): proxies
        """
        data = {identity: proxy}
        with Path.open(cls.path_to_proxies[identity], "w") as fh:
            json.dump(data, fh, indent=cls.indent_level)


class HttpProxies:
    """Hunt down http proxies"""

    def __init__(self):

        self.proxy_source: str = Basket.proxy_sources.get("SpeedX")
        self.proxy_list: list = []
        self.working_proxies: list = []
        self.identity = "http"

    def update_proxy_list(self):
        latest_proxy_list = Basket.fetch(
            self.proxy_source + "/http.txt", params={"raw": True}
        )
        self.proxy_list.extend(latest_proxy_list.text.split("\n"))

    def run(self):
        """Test proxies"""
        self.update_proxy_list()
        for proxy in self.proxy_list:
            is_proxy_working = Basket.check_status(proxy, "http")
            if is_proxy_working:
                self.working_proxies.append(proxy)
                Basket.save_proxy(
                    self.identity,
                    self.working_proxies,
                )


class Socks4Proxies:
    """Hunt down socks4 proxies"""

    def __init__(self):

        self.proxy_source: str = Basket.proxy_sources.get("SpeedX")
        self.proxy_list: list = []
        self.working_proxies: list = []
        self.identity = "socks4"

    def update_proxy_list(self):
        latest_proxy_list = Basket.fetch(
            self.proxy_source + "/socks4.txt", params={"raw": True}
        )
        self.proxy_list.extend(latest_proxy_list.text.split("\n"))

    def run(self):
        """Test proxies"""
        self.update_proxy_list()
        for proxy in self.proxy_list:
            is_proxy_working = Basket.check_status(proxy, self.identity)
            if is_proxy_working:
                self.working_proxies.append(proxy)
                Basket.save_proxy(
                    self.identity,
                    self.working_proxies,
                )



class Socks5Proxies:
    """Hunt down socks5 proxies"""

    def __init__(self):

        self.proxy_source: str = Basket.proxy_sources.get("SpeedX")
        self.proxy_list: list = []
        self.working_proxies: list = []
        self.identity = "socks5"

    def update_proxy_list(self):
        latest_proxy_list = Basket.fetch(
            self.proxy_source + "/socks5.txt", params={"raw": True}
        )
        self.proxy_list.extend(latest_proxy_list.text.split("\n"))

    def run(self):
        """Test proxies"""
        self.update_proxy_list()
        for proxy in self.proxy_list:
            is_proxy_working = Basket.check_status(proxy, self.identity)
            if is_proxy_working:
                self.working_proxies.append(proxy)
                Basket.save_proxy(
                    self.identity,
                    self.working_proxies,
                )

if __name__=="__main__":
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s : %(message)s",
        level=logging.INFO,
        datefmt="%d-%b-%Y %H:%M:%S",
    )
    from threading import Thread
    http_task = Thread(
        target = HttpProxies().run,
    )
    socks4_task = Thread(
        target=Socks4Proxies().run,
    )
    socks5_task = Thread(
        target=Socks5Proxies().run,
    )
    http_task.start()
    socks4_task.start()
    socks5_task.start()
    http_task.join()
    socks4_task.join()
    socks5_task.join()