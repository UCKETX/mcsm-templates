"""Collect the official Mohist API without publishing partial source data."""
from asyncio import gather
from datetime import datetime, timezone
from urllib.parse import quote

from ...utils import get_json, SyncLogger, update_database

API_URL = "https://api.mohistmc.com"
# The template market consumes these two projects. Removal requires review,
# rather than treating a missing upstream project as intentional retirement.
PROJECTS = ("mohist", "banner")
MAX_RETRIES = 3


class MohistSourceError(RuntimeError):
    pass


async def load_list(path, allow_empty=False):
    url = f"{API_URL}{path}"
    for attempt in range(MAX_RETRIES + 1):
        data = await get_json(url)
        if isinstance(data, list) and (data or allow_empty):
            return data
        SyncLogger.warning(f"MohistMC | Invalid/empty response from {url} (attempt {attempt + 1})")
    raise MohistSourceError(f"MohistMC collection failed: {url}; refusing partial data")


class SingleBuild:
    def __init__(self, name, version, build_info):
        number = build_info.get("id")
        if not isinstance(number, int) or isinstance(number, bool) or number < 0:
            raise MohistSourceError(f"{name} {version}: invalid build id")
        try:
            timestamp = datetime.fromisoformat(build_info["build_date"].replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError("missing timezone")
        except (KeyError, TypeError, AttributeError, ValueError) as error:
            raise MohistSourceError(f"{name} {version}: invalid build date") from error
        self.name, self.version = name, version
        self.build = f"build{number}"
        self.time = timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.url = (f"{API_URL}/project/{name.lower()}/{quote(version, safe='')}"
                    f"/builds/{number}/download")

    async def gather_single_build(self):
        return {"sync_time": self.time, "download_url": self.url,
                "core_type": self.name, "mc_version": self.version,
                "core_version": self.build}


class SingleVersion:
    def __init__(self, project_id, project_name, version):
        self.project_id, self.project_name, self.version = project_id, project_name, version
        self.builds = []

    async def load_self(self):
        data = await load_list(f"/project/{self.project_id}/{quote(self.version, safe='')}/builds", allow_empty=True)
        if not all(isinstance(item, dict) for item in data):
            raise MohistSourceError(f"{self.project_id} {self.version}: malformed builds")
        self.builds = [SingleBuild(self.project_name, self.version, item) for item in data]

    async def gather_version(self):
        return [await build.gather_single_build() for build in self.builds]


class Project:
    def __init__(self, project_id):
        self.project_id = project_id
        self.project_name = project_id.capitalize()
        self.versions = []

    async def load_self(self):
        data = await load_list(f"/project/{self.project_id}/versions")
        if not all(isinstance(item, dict) and isinstance(item.get("name"), str)
                   and item["name"].strip() for item in data):
            raise MohistSourceError(f"{self.project_id}: malformed versions")
        names = list(dict.fromkeys(item["name"] for item in data))
        self.versions = [SingleVersion(self.project_id, self.project_name, name) for name in names]
        await gather(*(version.load_self() for version in self.versions))
        self.versions = [version for version in self.versions if version.builds]
        if not self.versions:
            raise MohistSourceError(f"{self.project_id}: no downloadable builds")

    async def gather_project(self):
        return {version.version: await version.gather_version() for version in self.versions}


class MohistLoader:
    def __init__(self):
        self.project_list = []

    async def load_self(self):
        self.project_list = [Project(name) for name in PROJECTS]

    async def load_all_projects(self):
        if not self.project_list:
            raise MohistSourceError("MohistMC: no projects configured")
        # Validate the entire source before any DB writes. Do not swallow errors:
        # main.py -u must exit nonzero so Actions cannot generate/publish a release.
        await gather(*(project.load_self() for project in self.project_list))
        for project in self.project_list:
            for version, builds in (await project.gather_project()).items():
                update_database("runtime", project.project_name, version, builds=builds)
        SyncLogger.success("MohistMC | All projects collected successfully")
