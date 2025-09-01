from ...utils import get_json, update_database
from ...utils.minecraft import sort_versions_descending
from asyncio import create_task

class ForgeLoader:
    def __init__(self):
        self.mc_version_list: list = []
        self.total_info: dict[str, str] = {}
        self.tmp_info: dict[str, str] = {}

    async def load_self(self):
        mc_versions = await get_json(
            "https://bmclapi2.bangbang93.com/forge/minecraft"
        )
        # 按版本号降序排序
        self.mc_version_list = sort_versions_descending(mc_versions)
        tasks = [
            create_task(self.fetch_single_mc_version(mc_version=mc_version))
            for mc_version in self.mc_version_list
        ]
        for task in tasks:
            await task
        del tasks, self.mc_version_list
        for mc_version, builds in self.total_info.items():
            if mc_version == "1.7.10_pre4":
                continue
            else:
                update_database("runtime", "Forge", mc_version, builds=builds)

    async def fetch_single_mc_version(self, mc_version: str):
        tmp_info = await get_json(
            f"https://bmclapi2.bangbang93.com/forge/minecraft/{mc_version}"
        )
        self.total_info[mc_version] = []
        self.tmp_info[mc_version] = [await create_task(self.serialize_single_build(build)) for build in tmp_info]
        builds = [build for build in self.tmp_info[mc_version] if build is not None]
        # 按构建版本降序排序（根据 core_version 字段）
        builds.sort(key=lambda x: x.get('core_version', ''), reverse=True)
        self.total_info[mc_version] = builds
        del tmp_info

    async def serialize_single_build(self, single_info: dict):
        if single_info["build"] > 752 and single_info["build"] not in [960, 961, 963, 964]:
            return {
                "sync_time": single_info["modified"][:-5] + "Z",
                "download_url": f"https://bmclapi2.bangbang93.com/forge/download/{single_info["build"]}",
                "core_type": "Forge",
                "mc_version": single_info["mcversion"],
                "core_version": single_info["version"],
            }
        else:
            return None