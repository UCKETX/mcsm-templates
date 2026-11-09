import unittest
from unittest.mock import patch
from src.handler.mohistmc.base import MohistLoader, MohistSourceError, SingleBuild

BUILD = {"id": 950, "build_date": "2026-10-20T20:42:39Z"}


class MohistTests(unittest.IsolatedAsyncioTestCase):
    async def collect(self, bad_url=None, bad_data=None):
        async def response(url):
            if bad_url and bad_url in url:
                return bad_data
            return [{"name": "1.20.1"}] if url.endswith('/versions') else [BUILD]
        loader = MohistLoader()
        await loader.load_self()
        with patch('src.handler.mohistmc.base.get_json', side_effect=response), patch(
            'src.handler.mohistmc.base.update_database'
        ) as save:
            if bad_url:
                with self.assertRaises(MohistSourceError):
                    await loader.load_all_projects()
                save.assert_not_called()
            else:
                await loader.load_all_projects()
                self.assertEqual(save.call_count, 2)
                self.assertEqual(save.call_args_list[0].kwargs['builds'][0]['download_url'],
                                 'https://api.mohistmc.com/project/mohist/1.20.1/builds/950/download')

    async def test_new_api_collects_both_projects(self):
        await self.collect()

    async def test_failed_empty_or_malformed_project_aborts_all_writes(self):
        for data in (None, [], {}, [{"oops": "missing name"}]):
            with self.subTest(data=data):
                await self.collect('/banner/versions', data)

    async def test_failed_or_malformed_builds_abort_all_writes(self):
        for data in (None, [], {}, [None], [{}], [{"id": 1}],
                     [{"id": True, "build_date": BUILD['build_date']}],
                     [{"id": 1, "build_date": "not a date"}]):
            with self.subTest(data=data):
                await self.collect('/banner/1.20.1/builds', data)

    async def test_build_timestamp_and_identity_are_deterministic(self):
        build = await SingleBuild('Mohist', '1.20.1', BUILD).gather_single_build()
        self.assertEqual(build['sync_time'], BUILD['build_date'])
        self.assertEqual(build['core_version'], 'build950')

    async def test_uninitialized_loader_fails(self):
        with self.assertRaises(MohistSourceError):
            await MohistLoader().load_all_projects()
