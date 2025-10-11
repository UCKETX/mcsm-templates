from ...utils import get_json, SyncLogger, update_database
from traceback import format_exception
from asyncio import create_task


class _ProjectList(object):
    def __init__(self) -> None:
        self.project_id_list: list = []
        self.project_list: list = []

    async def load_self(self, retry: int = 0) -> None:
        # fmt: off
        if retry:
            SyncLogger.warning("SpongePowered | Retrying getting project list...")
        tmp_data = await get_json("https://dl-api.spongepowered.org/v2/groups/org.spongepowered/artifacts")
        if not isinstance(tmp_data, dict):
            SyncLogger.error("SpongePowered | Project list load failed (bad response)!")
            await self.load_self(retry=(retry+1))
            return
        self.project_id_list = tmp_data.get("artifactIds", [])
        if not self.project_id_list:
            SyncLogger.error("SpongePowered | Project list is empty!")
            await self.load_self(retry=(retry+1))
            return
        # fmt: on

    async def load_all_projects(self) -> None:
        tasks = [
            create_task(self.load_single_project(project_id=project_id))
            for project_id in self.project_id_list
        ]
        for task in tasks:
            await task
        del tasks

    async def load_single_project(self, project_id: str) -> None:
        try:
            p = Project(project_id=project_id)
            await p.load_self()
            self.project_list.append(p)
        except Exception as e:
            SyncLogger.warning(
                "{project_id} | Failed to load project!".format(
                    project_id=project_id.capitalize()
                )
            )
            SyncLogger.error("".join(format_exception(e)))
        SyncLogger.success(
            "{project_id} | All versions were loaded.".format(
                project_id=project_id.capitalize()
            )
        )


class Project(object):
    def __init__(self, project_id: str) -> None:
        self.project_id: str = project_id
        self.project_name: str = ""
        self.version_label_list: list = []
        self.versions: list[SingleVersion] = []

    async def load_self(self, retry: int = 0) -> None:
        if retry:
            SyncLogger.warning(
                "{project_id} | Retrying getting project info..."
            )
        tmp_data = await get_json(
            "https://dl-api.spongepowered.org/v2/groups/org.spongepowered/artifacts/{project_id}".format(
                project_id=self.project_id
            )
        )
        if not isinstance(tmp_data, dict):
            SyncLogger.error(
                "{project_id} | Project info load failed (bad response)!".format(
                    project_id=self.project_id.capitalize()
                )
            )
            await self.load_self(retry=(retry + 1))
            return
        # ensure non-None string assignment for typed attribute
        self.project_name = str(tmp_data.get("displayName") or "")
        self.version_label_list = (
            tmp_data.get("tags", {}).get("minecraft", [])
        )

        if not self.project_name or not self.version_label_list:
            SyncLogger.error(
                "{project_id} | Project info load failed!".format(
                    project_id=self.project_id.capitalize()
                )
            )
            await self.load_self(retry=(retry + 1))
            return
        await self.load_version_list()

    async def load_version_list(self) -> None:
        tasks = [
            create_task(self.load_single_version(version=version))
            for version in self.version_label_list
        ]
        for task in tasks:
            await task
        del tasks
        dict_info = await self.gather_project()
        for mc_version, builds in dict_info.items():
            update_database("runtime", self.project_name, mc_version, builds=builds)

    async def load_single_version(self, version: str) -> None:
        sv = SingleVersion(
            project_id=self.project_id, project_name=self.project_name, version=version
        )
        try:
            await sv.load_self()
        except Exception as e:
            SyncLogger.warning(
                "{project_name} | {version} | Failed to load version list!".format(
                    project_name=self.project_name, version=version
                )
            )
            SyncLogger.error("".join(format_exception(e)))
        self.versions.append(sv)

    async def gather_project(self) -> dict:
        return {
            version.version: await version.gather_version() for version in self.versions
        }


class SingleVersion(object):
    def __init__(self, project_id: str, project_name: str, version: str) -> None:
        self.project_id: str = project_id
        self.project_name: str = project_name
        self.version: str = version
        self.build_label_list: list = []
        self.builds_manager: BuildsManager | None = None

    async def load_self(self, retry: int = 0) -> None:
        if retry:
            SyncLogger.warning(
                "{project_id} | {version} | Retrying getting version info..."
            )
        tmp_data = await get_json(
            "https://dl-api.spongepowered.org/v2/groups/org.spongepowered/artifacts/{project_id}/versions?tags=,minecraft:{version}&offset=0&limit=10".format(
                project_id=self.project_id, version=self.version
            )
        )
        if not isinstance(tmp_data, dict):
            SyncLogger.error(
                "{project_id} | {version} | Failed to get version info (bad response)!".format(
                    project_id=self.project_id.capitalize(), version=self.version
                )
            )
            await self.load_self(retry=(retry + 1))
            return

        artifacts = tmp_data.get("artifacts", None)
        if isinstance(artifacts, dict):
            self.build_label_list = list(artifacts)
        elif isinstance(artifacts, list):
            # 若 API 返回列表，直接使用其内容作为标签列表
            self.build_label_list = artifacts
        else:
            self.build_label_list = []

        if not self.build_label_list:
            SyncLogger.error(
                "{project_id} | {version} | Failed to get version info!".format(
                    project_id=self.project_id.capitalize(), version=self.version
                )
            )
            await self.load_self(retry=(retry + 1))
            return

        self.builds_manager = BuildsManager(
            project_name=self.project_name,
            project_id=self.project_id,
            version=self.version,
            build_label_list=self.build_label_list,
        )
        await self.load_builds()

    async def load_builds(self) -> None:
        if self.builds_manager is None:
            return
        await create_task(self.builds_manager.load_self())

    async def gather_version(self) -> list:
        if self.builds_manager is None:
            return []
        return await self.builds_manager.gather_builds()


class BuildsManager(object):
    def __init__(
        self, project_name: str, project_id: str, version: str, build_label_list: list
    ) -> None:
        self.project_name: str = project_name
        self.project_id: str = project_id
        self.version: str = version
        self.build_label_list: list = build_label_list
        self.builds: list = []

    async def load_self(self) -> None:
        builds = []
        for build_label in self.build_label_list:
            tmp = await get_json(
                "https://dl-api.spongepowered.org/v2/groups/org.spongepowered/artifacts/{project_id}/versions/{build_label}".format(
                    project_id=self.project_id, build_label=build_label
                )
            )
            if isinstance(tmp, dict):
                builds.append(tmp)
            else:
                SyncLogger.warning(
                    "{project_name} | {version} | Build '{build_label}' response invalid, skipped.".format(
                        project_name=self.project_name, version=self.version, build_label=build_label
                    )
                )
        self.builds = builds

    async def get_universal_build(self, build_assets: list) -> str | None:
        if build_assets is None:
            SyncLogger.warning(
                "Fuck you SpongePowered! You didn't synchronized your motherfuckers old API!"
            )
            return None
        else:
            try:
                return [
                    asset["downloadUrl"]
                    for asset in build_assets
                    if asset["classifier"] == "universal"
                ][0]
            except IndexError:
                try:
                    return [
                        asset["downloadUrl"]
                        for asset in build_assets
                        if (not asset["classifier"] and asset["extension"] != "pom")
                    ][0]
                except IndexError:
                    SyncLogger.warning(
                        "Fuck you SpongePowered! You didn't built anything for this version!"
                    )
                    return None

    async def gather_builds(self) -> list:
        tmp_list = []
        for build_info in self.builds:
            if not isinstance(build_info, dict):
                continue
            universal_url = await self.get_universal_build(build_info.get("assets", None))
            if universal_url is not None:
                tmp_list.append(
                    {
                        "sync_time": "1970-01-01T00:00:00Z",
                        "download_url": universal_url,
                        "core_type": self.project_name,
                        "mc_version": str(self.version),
                        "core_version": (
                            str(
                                build_info.get("coordinates", {})
                                .get("version", "")
                                .replace(str(self.version + "-"), "")
                            )
                            if build_info.get("coordinates", None) is not None
                            else None
                        ),
                    }
                )
            else:
                continue
        return tmp_list


SpongePoweredLoader = _ProjectList
