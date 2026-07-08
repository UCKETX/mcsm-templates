from .network import get_json
from .logger import SyncLogger


class JenkinsCISerializer:
    def __init__(self, end_point: str):
        self.end_point = end_point

    @SyncLogger.catch
    async def get_jobs(self) -> list[dict[str, str]]:
        tmp_jobs = await get_json(f"{self.end_point}/api/json?tree=jobs[name,url]")  # type: dict[str, str]
        if not isinstance(tmp_jobs, dict) or not isinstance(tmp_jobs.get("jobs"), list):
            SyncLogger.warning(f"Jenkins jobs response invalid for {self.end_point}")
            return []
        return [
            {key: value for key, value in job.items() if key != "_class"}
            for job in tmp_jobs["jobs"]
        ]

    @SyncLogger.catch
    async def load_single_job(self, job_name: str) -> list[dict[str, str]]:
        tmp_builds = await get_json(
            f"{self.end_point}/job/{job_name}/api/json?tree=builds[number,timestamp,status,result,artifacts[fileName,relativePath]]"
        )  # type: dict[str, str]
        if not isinstance(tmp_builds, dict) or not isinstance(tmp_builds.get("builds"), list):
            SyncLogger.warning(f"Jenkins builds response invalid for {self.end_point}/job/{job_name}")
            return []
        result = []
        for build in tmp_builds["builds"]:
            if build.get("result") == "SUCCESS":
                result.append(
                    {key: value for key, value in build.items() if key != "_class"}
                )
        return result
