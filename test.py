from requests import get

resp = get(
    "https://example.com",
    proxies={
        "https": "https://193.109.79.209:44499",
    },
)

print(resp.status_code)
