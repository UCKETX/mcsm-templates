from ...utils import GitHubReleaseSerializer, SyncLogger, update_database


class CatServerReleaseSerializer(GitHubReleaseSerializer):
    def __init__(self) -> None:
        super().__init__(owner="Luohuayu", repo="CatServer")

    async def get_assets(self) -> None:
        await self.get_release_data()
        # 当无法获取到 Release 数据时（网络错误或无发布），直接返回并记录告警
        if not self.release_list:
            SyncLogger.warning("CatServer | No release data found.")
            return

        for release in self.release_list:
            try:
                release["core_type"] = "CatServer"
                release["mc_version"] = release["target_commitish"]
                release["core_version"] = release["tag_name"]
                release.pop("tag_name")
                release.pop("name")
                release.pop("target_commitish")
            except (KeyError, ValueError) as e:
                SyncLogger.warning(
                    f"CatServer | Failed to normalize release {release.get('tag_name', 'unknown')}: {e}"
                )

        catserver_res = await self.sort_by_mc_versions()
        if catserver_res:
            for mc_version, builds in catserver_res.items():
                update_database("runtime", "CatServer", mc_version, builds=builds)
            SyncLogger.success("CatServer | All versions were loaded.")
        else:
            SyncLogger.warning("CatServer | No versions found or API response is empty.")
