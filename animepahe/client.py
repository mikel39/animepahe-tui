import httpx

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'


clt = httpx.AsyncClient(
    timeout=60.0,
    headers={'user-agent': USER_AGENT},
    transport=httpx.AsyncHTTPTransport(retries=10),
)
