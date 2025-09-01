from .base import VanillaLoader
from ...utils import SyncLogger


async def vanilla_runner() -> None:
    import time

    start = time.perf_counter()

    loader = VanillaLoader()
    await loader.load_versions()

    SyncLogger.info(
        f"Vanilla | Elapsed time: {time.perf_counter() - start:.2f}s."
    )