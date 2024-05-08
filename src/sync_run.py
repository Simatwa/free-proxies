import requests
import logging
import typing
import threading
import json
import datetime
from pathlib import Path

request_timeout = 5

indentation_level = 4

thread_amount = 22

proxy_dir = Path(__file__).parents[1] / "files"

path_to_proxies: dict[str, Path] = {
    "http": proxy_dir / "http.json",
    "socks4": proxy_dir / "socks4.json",
    "socks5": proxy_dir / "socks5.json",
    "proxies": proxy_dir / "proxies.json",
}

test_proxy_url = (
    "https://raw.githubusercontent.com/Simatwa/free-proxies/master/files/test.md"
)

working_proxy_cache: dict[str, list[str]] = {
    "http": [],
    "socks4": [],
    "socks5": [],
}

session = requests.Session()
session.headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Accept": "*/*",
}


def fetch(*args, **kwargs) -> requests.Response:
    return session.get(
        *args,
        **kwargs,
        timeout=request_timeout,
    )


def get_proxies() -> dict[str, list[str]]:
    http_proxies = fetch(
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
    ).text.split("\n")
    logging.info(f"Total http proxies {len(http_proxies)}")
    socks4_proxies = fetch(
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt"
    ).text.split("\n")
    logging.info(f"Total socks4 proxies {len(socks4_proxies)}")
    socks5_proxies = fetch(
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
    ).text.split("\n")
    logging.info(f"Total socks5 proxies {len(socks5_proxies)}")
    logging.warning(
        f"Maximum running time {str(datetime.timedelta(seconds=(len(http_proxies+socks4_proxies+socks5_proxies)/thread_amount)*request_timeout)).split('.')[0].zfill(8)}"
    )
    return dict(http=http_proxies, socks4=socks4_proxies, socks5=socks5_proxies)


def test_proxy(proxy_type: str, proxy) -> typing.NoReturn:
    try:
        resp = fetch(test_proxy_url, proxies=dict(https=f"{proxy_type}://{proxy}"))
        resp.raise_for_status()
        if resp.ok:
            logging.info(f"Working proxy ({proxy_type}, {proxy})")
            working_proxy_cache[proxy_type].append(proxy)
    except Exception as e:
        logging.error(
            f"Failed ({proxy_type}, {proxy}) - {e.args[1] if e.args and len(e.args)>1 else e}"
        )


def save_proxies():
    for proxy_type, proxies in working_proxy_cache.items():
        with Path.open(path_to_proxies[proxy_type], "w") as fh:
            json.dump(dict(proxies=proxies), fh, indent=indentation_level)
    # combined
    with Path.open(path_to_proxies["proxies"], "w") as fh:
        json.dump(working_proxy_cache, fh, indent=indentation_level)


def main():
    for proxy_type, proxies in get_proxies().items():
        tasks: list[threading.Thread] = []
        for index, proxy in enumerate(proxies, start=1):
            task = threading.Thread(target=test_proxy, args=(proxy_type, proxy))
            if index % thread_amount == 0:
                logging.warning(
                    f"Waiting currrent running {thread_amount} threads to complete."
                )
                for running_task in tasks:
                    running_task.join()
                tasks.clear()
            else:
                tasks.append(task)
                task.start()
    save_proxies()


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s : %(message)s",
        level=logging.INFO,
        datefmt="%d-%b-%Y %H:%M:%S",
    )
    try:
        main()
    except KeyboardInterrupt:
        print("[*] Surrendering to the master.")
