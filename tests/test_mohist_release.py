import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from validate_mohist_release import validate

class MohistReleaseTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.old, self.new = (Path(tmp.name) / name for name in ('old.json', 'new.json'))
        self.packages = [{'category': name, 'title': f'{name} 1.20.1', 'targetLink': 'old'}
                         for name in ('Mohist', 'Banner')]
        self.write(self.old, self.packages)

    def write(self, path, packages):
        path.write_text(json.dumps({'packages': packages}))

    def test_missing_source_fails_even_with_already_damaged_baseline(self):
        self.write(self.old, [])
        self.write(self.new, [])
        with self.assertRaises(ValueError):
            validate(self.old, self.new)

    def test_partial_version_loss_fails_without_rewriting(self):
        self.write(self.old, self.packages + [{'category': 'Banner', 'title': 'Banner 1.19.4'}])
        self.write(self.new, self.packages)
        original = self.new.read_bytes()
        with self.assertRaises(ValueError):
            validate(self.old, self.new)
        self.assertEqual(self.new.read_bytes(), original)

    def test_new_downloads_pass(self):
        self.write(self.new, [{**p, 'targetLink': 'new'} for p in self.packages])
        validate(self.old, self.new)

    def test_reviewed_version_retirement_passes(self):
        self.write(self.old, self.packages + [{'category': 'Banner', 'title': 'Banner 1.19.4'}])
        self.write(self.new, self.packages)
        with patch('validate_mohist_release.RETIRED_PACKAGES', {('Banner', 'Banner 1.19.4')}):
            validate(self.old, self.new)
