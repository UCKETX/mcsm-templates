import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyze_changes import analyze_changes
from preserve_pufferfish import preserve_pufferfish
from src.handler.pufferfish.base import PufferfishCISerializer


class PufferfishCollectorTests(unittest.IsolatedAsyncioTestCase):
    async def collect(self, last_job, empty=False):
        serializer = PufferfishCISerializer()
        jobs = {
            "Pufferfish-1.18": ("1.18.1", "1.18.2"),
            "Pufferfish-1.19": ("1.19.1", "1.19.2", "1.19.3", "1.19.4"),
        }
        first_finished = asyncio.Event()

        async def load_job(job_name):
            if job_name == last_job:
                await first_finished.wait()
                if empty:
                    return []
            else:
                first_finished.set()
            return [
                {
                    "number": number,
                    "timestamp": 0,
                    "artifacts": [{
                        "fileName": f"pufferfish-paperclip-{version}.jar",
                        "relativePath": f"build/libs/pufferfish-paperclip-{version}.jar",
                    }],
                }
                for number, version in enumerate(jobs[job_name], start=1)
            ]

        await serializer.serialize_project_name([
            {"name": name, "url": f"{serializer.end_point}/job/{name}/"}
            for name in jobs
        ])
        with patch.object(serializer, "load_single_job", side_effect=load_job):
            await serializer.load_versions()
        return set(serializer.job_data["Pufferfish"])

    async def test_combines_jobs_in_either_completion_order(self):
        expected = {"1.18.1", "1.18.2", "1.19.1", "1.19.2", "1.19.3", "1.19.4"}
        for last_job in ("Pufferfish-1.18", "Pufferfish-1.19"):
            with self.subTest(last_job=last_job):
                self.assertEqual(await self.collect(last_job), expected)

    async def test_late_empty_job_preserves_sibling_results(self):
        self.assertEqual(
            await self.collect("Pufferfish-1.19", empty=True), {"1.18.1", "1.18.2"}
        )


class PufferfishReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_dir.cleanup)
        self.previous = Path(temporary_dir.name) / "previous.json"
        self.current = Path(temporary_dir.name) / "current.json"
        self.old_package = {
            "category": "Pufferfish", "title": "Pufferfish 1.18.2", "targetLink": "old"
        }
        self.write_snapshot(self.previous, [self.old_package])

    def write_snapshot(self, path, packages):
        path.write_text(json.dumps({"packages": packages}), encoding="utf-8")

    def test_missing_package_does_not_show_as_removed(self):
        self.write_snapshot(self.current, [])
        preserve_pufferfish(self.previous, self.current)
        self.assertEqual(json.loads(self.current.read_text())["packages"], [self.old_package])
        stats, _ = analyze_changes(self.previous, self.current)
        self.assertEqual(stats["removed_versions"], 0)

    def test_fresh_build_wins(self):
        updated = {**self.old_package, "targetLink": "new"}
        self.write_snapshot(self.current, [updated])
        preserve_pufferfish(self.previous, self.current)
        self.assertEqual(json.loads(self.current.read_text())["packages"], [updated])

    def test_explicit_retirement_removes_even_current_package(self):
        self.write_snapshot(self.current, [self.old_package])
        with patch("preserve_pufferfish.RETIRED_PACKAGES", {("Pufferfish", "Pufferfish 1.18.2")}):
            preserve_pufferfish(self.previous, self.current)
        self.assertEqual(json.loads(self.current.read_text())["packages"], [])

    def test_invalid_baseline_fails_before_rewriting(self):
        self.previous.write_text("{}", encoding="utf-8")
        self.write_snapshot(self.current, [])
        original = self.current.read_bytes()
        with self.assertRaises(ValueError):
            preserve_pufferfish(self.previous, self.current)
        self.assertEqual(self.current.read_bytes(), original)
