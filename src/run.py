# fetch list, http, socks4, sock5
# iterate over and test each
import httpx
import typing
import logging
import json
import asyncio
from pathlib import Path


class Basket:

    request_headers: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Accept": "*/*",
    }
    proxy_sources: dict[str, str] = {
        "SpeedX": "https://github.com/TheSpeedX/PROXY-List"
    }

    request_timeout: int = 5

    indent_level: int = 3

    proxy_dir = Path(__file__).parents[1] / "files"

    path_to_proxies: dict[str, Path] = {
        "http": proxy_dir / "http.json",
        "socks4": proxy_dir / "sock4.json",
        "socks5": proxy_dir / "socks5.json",
    }

    test_resource_url: str = (
        "https://github.com/Simatwa/free-proxies/blob/master/files/test.md"
    )

    @classmethod
    async def fetch(cls, url: str, **kwargs) -> httpx.Response:
        """ "Make Get request

        Args:
            url (str): Path to resource.
            kwargs : Request parameters.

        Returns:
            httpx.Response: response
        """
        async with httpx.AsyncClient(
            headers=Basket.request_headers, follow_redirects=True, **kwargs
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response

    @classmethod
    async def check_status(
        cls, proxy: str, type: typing.Literal["https", "socks4", "socks5"]
    ) -> bool:
        """Test working status of proxy

        Args:
            proxy (str): host:port
            type (typing.Literal["https", "socks4", "socks5"]):

        Returns:
            bool: is proxy working?
        """
        proxy_in_dict = {"https://": f"{type}://{proxy}"}
        try:
            resp = await cls.fetch(
                Basket.test_resource_url, params={"raw": True}, proxy=proxy_in_dict
            )
            assert resp.is_success == True, f"{proxy} not working"
            logging.info(f"Working proxy : ({type}, {proxy})")
            return True
        except Exception as e:
            logging.error(
                f'[{proxy_in_dict['https://']}] {e.args[1] if e.args and len(e.args)>1 else e}'
            )

    @classmethod
    async def save_proxy(
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

        self.proxy_source: str = Basket.proxy_sources.get("SpeedX") + "/blob/master"
        self.proxy_list: list = []
        self.working_proxies: list = []
        self.identity = "http"

    async def update_proxy_list(self):
        latest_proxy_list = await Basket.fetch(
            self.proxy_source + "/http.txt", params={"raw": True}
        )
        self.proxy_list.extend(latest_proxy_list.text.split("\n"))

    async def run(self):
        """Test proxies"""
        await self.update_proxy_list()
        for proxy in self.proxy_list:
            is_proxy_working = await Basket.check_status(proxy, "https")
            if is_proxy_working:
                self.working_proxies.append(proxy)
                await Basket.save_proxy(
                    self.identity,
                    self.proxy_list,
                )


class Socks4Proxies:
    """Hunt down http proxies"""

    def __init__(self):

        self.proxy_source: str = Basket.proxy_sources.get("SpeedX") + "/blob/master"
        self.proxy_list: list = []
        self.working_proxies: list = []
        self.identity = "socks4"

    async def update_proxy_list(self):
        latest_proxy_list = await Basket.fetch(
            self.proxy_source + "/socks4.txt", params={"raw": True}
        )
        self.proxy_list.extend(latest_proxy_list.text.split("\n"))

    async def run(self):
        """Test proxies"""
        await self.update_proxy_list()
        for proxy in self.proxy_list:
            is_proxy_working = await Basket.check_status(proxy, self.identity)
            if is_proxy_working:
                self.working_proxies.append(proxy)
                await Basket.save_proxy(
                    self.identity,
                    self.proxy_list,
                )


class Socks5Proxies:
    """Hunt down http proxies"""

    def __init__(self):

        self.proxy_source: str = Basket.proxy_sources.get("SpeedX") + "/blob/master"
        self.proxy_list: list = []
        self.working_proxies: list = []
        self.identity = "socks5"

    async def update_proxy_list(self):
        latest_proxy_list = await Basket.fetch(
            self.proxy_source + "/socks5.txt", params={"raw": True}
        )
        self.proxy_list.extend(latest_proxy_list.text.split("\n"))

    async def run(self):
        """Test proxies"""
        await self.update_proxy_list()
        for proxy in self.proxy_list:
            is_proxy_working = await Basket.check_status(proxy, self.identity)
            if is_proxy_working:
                self.working_proxies.append(proxy)
                await Basket.save_proxy(
                    self.identity,
                    self.proxy_list,
                )


async def main():
    tasks = [
        asyncio.create_task(HttpProxies().run()),
        asyncio.create_task(Socks4Proxies().run()),
        asyncio.create_task(Socks5Proxies().run()),
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s : %(message)s",
        level=logging.INFO,
        datefmt="%d-%b-%Y %H:%M:%S",
    )
    asyncio.run(main())
