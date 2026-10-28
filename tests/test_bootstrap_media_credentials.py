import json
import os
from pathlib import Path
import stat
import tempfile
import unittest

from scripts.bootstrap_media_credentials import find_vivint_entry, write_secret_json


class BootstrapMediaCredentialsTests(unittest.TestCase):
    def test_find_vivint_entry_requires_exactly_one_entry(self) -> None:
        storage = {
            "data": {
                "entries": [
                    {"domain": "met", "data": {}},
                    {"domain": "vivint", "data": {"username": "example"}},
                ]
            }
        }

        entry = find_vivint_entry(storage)

        self.assertEqual(entry["data"]["username"], "example")

    def test_write_secret_json_creates_mode_0600_and_will_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "media.json"
            write_secret_json(path, {"secret": "value"})

            self.assertEqual(json.loads(path.read_text()), {"secret": "value"})
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                write_secret_json(path, {"secret": "replacement"})


if __name__ == "__main__":
    unittest.main()
