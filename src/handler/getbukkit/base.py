from datetime import datetime
from lxml import html
from ...utils import SyncLogger, get_text, update_database


class GetBukkitParser:
    def __init__(self, core_type: str):
        self.core_type = core_type

    async def convert_to_ISO8601(self, date_string):
        return (
            datetime.strptime(date_string, "%A, %B %d %Y")
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .isoformat()
            + "Z"
        )

    async def get_version_list(self):
        try:
            page_content = await get_text(f"https://getbukkit.org/download/{self.core_type}")
            if page_content is None:
                SyncLogger.error(f"{self.core_type.capitalize()} | Failed to fetch page content, skipping...")
                return
            
            root = html.fromstring(page_content)
        except Exception as e:
            SyncLogger.error(f"{self.core_type.capitalize()} | Error parsing HTML: {e}, skipping...")
            return

        versions = {}

        download_panes = root.xpath('//div[@class="download-pane"]')
        for pane in download_panes:
            try:
                version = pane.xpath(".//h2/text()")[0]
                sync_time = pane.xpath(".//h3/text()")[1]

                versions[version.strip()] = []

                download_url = await self.get_real_download_link(
                    pane.xpath('.//a[@class="btn btn-download"]/@href')[0]
                )
                
                if download_url is None:
                    SyncLogger.warning(f"{self.core_type.capitalize()} | Failed to get download URL for version {version.strip()}, skipping...")
                    continue

                versions[version.strip()].append(
                    {
                        "sync_time": await self.convert_to_ISO8601(sync_time.strip()),
                        "download_url": download_url,
                        "core_type": self.core_type.capitalize(),
                        "mc_version": version.strip(),
                        "core_version": "Latest",
                    }
                )
            except Exception as e:
                SyncLogger.warning(f"{self.core_type.capitalize()} | Error processing version pane: {e}, skipping this version...")
                continue
        
        await self.save_data(versions)

    async def get_real_download_link(self, url):
        try:
            page_content = await get_text(url)
            if page_content is None:
                SyncLogger.warning(f"{self.core_type.capitalize()} | Failed to fetch download page content for URL: {url}")
                return None
            
            download_links = html.fromstring(page_content).xpath(
                '//div[@class="well"]//h2/a/@href'
            )
            
            if not download_links:
                SyncLogger.warning(f"{self.core_type.capitalize()} | No download link found on page: {url}")
                return None
                
            return download_links[0]
        except Exception as e:
            SyncLogger.warning(f"{self.core_type.capitalize()} | Error getting real download link from {url}: {e}")
            return None

    async def save_data(self, data_dict: dict):
        for mc_version, builds in data_dict.items():
            update_database("runtime", self.core_type.capitalize(), mc_version, builds=builds)
        SyncLogger.success(f"{self.core_type.capitalize()} | All versions were loaded.")
