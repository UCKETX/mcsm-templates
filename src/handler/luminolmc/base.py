from ...utils import GitHubReleaseSerializer, SyncLogger, update_database


class LuminolReleaseSerializer(GitHubReleaseSerializer):
    def __init__(self) -> None:
        super().__init__(owner="LuminolMC", repo="Luminol")

    async def get_assets(self) -> None:
        await self.get_release_data()
        idx: int = len(self.release_list)
        for release in self.release_list:
            release["core_type"] = "Luminol"
            # Tag names sometimes contain multiple hyphens; only the first part is the MC version.
            mc_part, _, _ = release["tag_name"].partition("-")
            release["mc_version"] = mc_part
            release["core_version"] = f"build{idx}"
            release.pop("tag_name")
            release.pop("target_commitish")
            release.pop("name")
            if release.get("download_url", None) is None:
                self.release_list.remove(release)
            idx -= 1

        luminol_res = await self.sort_by_mc_versions()

        if luminol_res:
            for mc_version, builds in luminol_res.items():
                update_database("runtime", "Luminol", mc_version, builds=builds)
            SyncLogger.success("Luminol | All versions were loaded.")
        else:
            SyncLogger.warning("Luminol | No versions found or API response is empty.")


class LightingLuminolReleaseSerializer(GitHubReleaseSerializer):
    def __init__(self) -> None:
        super().__init__(owner="LuminolMC", repo="LightingLuminol")

    async def get_assets(self) -> None:
        await self.get_release_data()
        idx: int = len(self.release_list)
        for release in self.release_list:
            release["core_type"] = "LightingLuminol"
            # Tag names sometimes contain multiple hyphens; only the first part is the MC version.
            mc_part, _, _ = release["tag_name"].partition("-")
            release["mc_version"] = mc_part
            release["core_version"] = f"build{idx}"
            release.pop("tag_name")
            release.pop("target_commitish")
            release.pop("name")
            if release.get("download_url", None) is None:
                self.release_list.remove(release)
            idx -= 1

        lighting_luminol_res = await self.sort_by_mc_versions()
        if lighting_luminol_res:
            for mc_version, builds in lighting_luminol_res.items():
                update_database("runtime", "LightingLuminol", mc_version, builds=builds)
            SyncLogger.success("LightingLuminol | All versions were loaded.")
        else:
            SyncLogger.warning(
                "LightingLuminol | No versions found or API response is empty."
            )
