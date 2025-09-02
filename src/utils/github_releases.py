from .network import get_json
from .logger import SyncLogger
from .minecraft import sort_versions_descending
from pandas import DataFrame


class GitHubReleaseSerializer(object):
    def __init__(self, owner: str, repo: str) -> None:
        self.api_link = "https://api.github.com/repos/{user}/{repo}/releases".format(
            user=owner, repo=repo
        )
        self.release_list: list[dict] = []

    @SyncLogger.catch
    async def get_release_data(self) -> None:
        tmp_data = await get_json(self.api_link)
        for data in tmp_data:
            self.release_list.append(
                {
                    "target_commitish": data["target_commitish"],
                    "name": data["name"],
                    "tag_name": data["tag_name"],
                    "sync_time": data["published_at"],
                    "assets": data["assets"],
                }
            )
        # 按版本号降序排序
        self.release_list = self.sort_releases_by_version(self.release_list)
        await self.load_assets()

    @SyncLogger.catch
    async def load_assets(self) -> None:
        for release in self.release_list:
            for asset in release["assets"]:
                release["download_url"] = (
                    "https://raw.bgithub.xyz/" + asset["browser_download_url"]
                )
            release.pop("assets")

    @SyncLogger.catch
    def sort_releases_by_version(self, releases: list[dict]) -> list[dict]:
        """按版本号降序排序 releases"""
        try:
            # 尝试按 tag_name 进行版本排序
            tag_names = [release["tag_name"] for release in releases]
            sorted_tags = sort_versions_descending(tag_names)
            
            # 创建排序映射
            tag_to_index = {tag: i for i, tag in enumerate(sorted_tags)}
            
            # 按排序后的顺序重新排列 releases
            return sorted(releases, key=lambda r: tag_to_index.get(r["tag_name"], len(sorted_tags)))
        except Exception as e:
            SyncLogger.warning(f"Failed to sort releases by version: {e}")
            # 如果排序失败，按发布时间降序排序
            return sorted(releases, key=lambda r: r["sync_time"], reverse=True)

    @SyncLogger.catch
    async def sort_by_mc_versions(self) -> dict:
        data_frame = DataFrame(self.release_list)
        groups = data_frame.groupby("mc_version").groups
        res = {}
        for version, indices in groups.items():
            version_releases = data_frame.loc[indices].to_dict("records")
            # 对每个 MC 版本的 releases 也进行排序
            version_releases = self.sort_releases_by_version(version_releases)
            res.update({version: version_releases})
        
        # 对 MC 版本键也进行降序排序
        sorted_versions = sort_versions_descending(list(res.keys()))
        return {version: res[version] for version in sorted_versions}
