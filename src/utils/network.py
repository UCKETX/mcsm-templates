from aiohttp import ClientSession
from .logger import __version__
from .logger import SyncLogger
from orjson import loads

@SyncLogger.catch
async def get_proxy() -> str | None:
    from urllib.request import getproxies

    try:
        proxy = getproxies()["http"]
    except KeyError:
        proxy = None
    del getproxies
    return proxy


@SyncLogger.catch
async def get_json(link: str) -> dict | list | None:
    # print(link)
    trust_env = bool(isinstance(await get_proxy(), str))
    async with ClientSession(
        trust_env=trust_env,
        headers={
            "User-Agent": f"MCSLSync/{__version__} Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        },
    ) as session:
        async with session.get(link) as response:
            return loads(await response.text())


@SyncLogger.catch
async def get_text(link: str) -> str | None:
    trust_env = bool(isinstance(await get_proxy(), str))
    async with ClientSession(
        trust_env=trust_env,
        headers={
            "User-Agent": f"MCSLSync/{__version__} Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        },
    ) as session:
        async with session.get(link) as response:
            try:
                return await response.text()
            except UnicodeDecodeError:
                # Try different encodings if UTF-8 fails
                try:
                    content = await response.read()
                    # Try common encodings
                    for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
                        try:
                            return content.decode(encoding)
                        except UnicodeDecodeError:
                            continue
                    # If all encodings fail, use errors='ignore'
                    return content.decode('utf-8', errors='ignore')
                except Exception as e:
                    SyncLogger.warning(f"Failed to decode response from {link}: {e}")
                    return None


async def check_file_exists(uri: str):
    async with ClientSession(
        trust_env=not bool(isinstance(await get_proxy(), str)),
        headers={
            "User-Agent": f"MCSLSync/{__version__} Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        },
    ) as session:
        async with session.head(
            uri, allow_redirects=True, max_redirects=10
        ) as head_response:
            if head_response.status in [302, 307]:
                redirect_uri = head_response.headers.get("Location")
                return await check_file_exists(redirect_uri)
            else:
                print(head_response.status)
                return True if not head_response.status != 404 else False
