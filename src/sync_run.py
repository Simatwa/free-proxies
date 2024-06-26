#!/usr/bin/python3
import requests
import logging
import typing
import threading
import json
import datetime
import random
import time
import os
from pathlib import Path

__version__ = "0.0.5"

request_timeout = 5

indentation_level = 4

thread_amount = 310

proxy_dir = Path(os.getcwd())

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
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt"
    ).text.split("\n")
    logging.info(f"Total socks4 proxies {len(socks4_proxies)}")
    socks5_proxies = fetch(
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt"
    ).text.split("\n")
    logging.info(f"Total socks5 proxies {len(socks5_proxies)}")
    logging.warning(
        f"Estimated running time {str(datetime.timedelta(seconds=(len(http_proxies+socks4_proxies+socks5_proxies)/thread_amount)*request_timeout)).split('.')[0].zfill(8)}"
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
        logging.debug(
            f"Failed ({proxy_type}, {proxy}) - {e.args[1] if e.args and len(e.args)>1 else e}"
        )


def generate_metadata() -> dict[str, dict[str, str]]:
    proxy_metadata: dict[str, dict[str, str]] = {}
    global request_timeout
    request_timeout = 3
    tasks: list[threading.Thread] = []

    def get_metadata(proxy):
        try:
            proxy = f"{proxy_type}://{proxy}"
            start_time = time.time()
            resp = fetch("http://ip-api.com/json", proxies=dict(http=proxy))
            response_time = time.time() - start_time
            proxy_info = resp.json()
            proxy_info["response_time"] = response_time
            proxy_metadata[proxy] = proxy_info
            logging.info(
                f"Metadata generated for {proxy}  ({proxy_info['country']} - {proxy_info['status']})"
            )
        except Exception as e:
            logging.debug(f"Error while generating metadata - {e}")

    for proxy_type, proxies in working_proxy_cache.items():
        logging.info(f"Generating metadata for {proxy_type} proxies - {len(proxies)}")
        for count, proxy in enumerate(proxies, start=1):
            try:
                task = threading.Thread(
                    target=get_metadata,
                    args=(proxy,),
                )
                tasks.append(task)
                task.start()
                if count % round(thread_amount / 4) == 0:
                    logging.info(
                        f"Waiting for current running {round(thread_amount/2)} threads to complete."
                    )
                    for task in tasks:
                        task.join()
                    tasks.clear()

            except Exception as e:
                if task in tasks:
                    tasks.remove(task)

                logging.debug(f"Fetching proxy ({proxy}) metadata failed - {e}")

    for task in tasks:
        task.join()

    return proxy_metadata


def save_proxies():
    def write(path: Path, data: dict):
        with Path.open(path, "w") as fh:
            json.dump(data, fh, indent=indentation_level)

    def select_random_proxies():
        random_proxies: list[str] = []
        for proxy_type, proxies in working_proxy_cache.items():
            if len(proxies) > 1:
                random_proxies.extend(
                    [
                        f"{proxy_type}://{proxy}"
                        for proxy in random.sample(
                            proxies, round((3 / 4) * len(proxies))
                        )
                    ]
                )
            elif proxies:
                random_proxies.append(f"{proxy_type}://{proxies[0]}")

        write(
            path_to_proxies["random"],
            dict(proxies=random.sample(random_proxies, len(random_proxies))),
        )

    for proxy_type, proxies in working_proxy_cache.items():
        write(path_to_proxies[proxy_type], dict(proxies=proxies))

    # combined
    write(path_to_proxies["proxies"], working_proxy_cache)

    write(path_to_proxies["metadata"], generate_metadata())

    select_random_proxies()
    write(
        proxy_dir / "timestamp.json",
        dict(utc=datetime.datetime.now(datetime.timezone.utc).__str__()),
    )


def main():
    tasks: list[threading.Thread] = []
    for proxy_type, proxies in get_proxies().items():
        for index, proxy in enumerate(proxies, start=1):
            task = threading.Thread(target=test_proxy, args=(proxy_type, proxy))
            tasks.append(task)
            task.start()
            if index % thread_amount == 0:
                logging.warning(
                    f"Waiting currrent running {thread_amount} threads to complete."
                )
                for running_task in tasks:
                    running_task.join()
                tasks.clear()

    for task in tasks:
        task.join()

    save_proxies()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="free-proxies",
        description="Generate free to use http, socks4 and socks5 proxies.",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s v{__version__}"
    )
    parser.add_argument(
        "threads",
        nargs="?",
        type=int,
        help="Threads for making requests - %(default)s",
        default=thread_amount,
    )
    parser.add_argument(
        "-t",
        "--timeout",
        metavar="INT",
        type=int,
        help="Http request timeout in seconds - %(default)s",
        default=request_timeout,
    )
    parser.add_argument(
        "-u",
        "--url",
        help="Url for testing the proxies - %(default)s",
        default=test_proxy_url,
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="DIR",
        help="Directory to save the generated contents - %(default)s",
        default=proxy_dir.as_posix(),
    )
    parser.add_argument(
        "-i",
        "--indent",
        metavar="INT",
        type=int,
        help="Indentation level for json outputs - %(default)s",
        default=indentation_level,
    )
    parser.add_argument(
        "-l",
        "--level",
        type=int,
        choices=[10, 20, 30, 40, 50, 51],
        metavar="10|20|30|40|50|51",
        help="Logging level",
        default=20,
    )
    parser.add_argument("-f", "--file", metavar="PATH", help="Path to file to log to.")
    parser.add_argument(
        "-m",
        "--mode",
        metavar="w|a",
        choices=["w", "a"],
        default="a",
        help="Logging file  mode - %(default)s",
    )
    args = parser.parse_args()
    if not Path(args.output).is_dir():
        print(f"Path '{args.output}' is not a valid directory.")
        import sys

        sys.exit(1)

    thread_amount = args.threads
    request_timeout = args.timeout
    indentation_level = args.indent

    proxy_dir = Path(args.output)

    test_proxy_url = args.url

    path_to_proxies: dict[str, Path] = {
        "http": proxy_dir / "http.json",
        "socks4": proxy_dir / "socks4.json",
        "socks5": proxy_dir / "socks5.json",
        "proxies": proxy_dir / "proxies.json",
        "random": proxy_dir / "random.json",
        "metadata": proxy_dir / "metadata.json",
    }

    log_handlers = [logging.StreamHandler()]

    if args.file:
        log_handlers.append(logging.FileHandler(args.file, args.mode))

    logging.basicConfig(
        format="%(asctime)s - %(levelname)s : %(message)s",
        level=args.level,
        datefmt="%d-%b-%Y %H:%M:%S",
        handlers=log_handlers,
    )
    try:
        main()
    except KeyboardInterrupt:
        print("[*] Surrendering to the master.")
