"""A reply that lands after a run is picked up by the next run without a full rebuild."""
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LATE_ROW = "2026-09-01 reply privacy@octaneai.com\n"


def dbt(args, raw_dir, db):
    env = dict(os.environ, GTM_TEST_DB=str(db))
    subprocess.run(
        ["uv", "run", "dbt", *args, "--target", "test", "--vars", f"{{raw_dir: '{raw_dir}'}}"],
        cwd=ROOT, env=env, check=True, capture_output=True, text=True,
    )


def count(db, sql):
    out = subprocess.run(["duckdb", str(db), "-csv", "-noheader", "-c", sql],
                         capture_output=True, text=True, check=True).stdout.strip()
    return int(out)


class LateReply(unittest.TestCase):
    def test_late_reply_is_captured_on_next_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = pathlib.Path(tmp) / "raw"
            shutil.copytree(ROOT / "raw" / "latest", raw)
            db = pathlib.Path(tmp) / "test.duckdb"
            replies = raw / "replies.txt"
            full = replies.read_text()
            self.assertIn(LATE_ROW, full)
            replies.write_text(full.replace(LATE_ROW, ""))

            dbt(["build"], raw, db)
            before = count(db, "select count(*) from fact_replies")
            self.assertEqual(count(db, "select count(*) from fact_replies where is_human_reply"), 0)

            replies.write_text(full)
            dbt(["run", "--select", "fact_replies"], raw, db)
            self.assertEqual(count(db, "select count(*) from fact_replies"), before + 1)
            self.assertEqual(count(db, "select count(*) from fact_replies where is_human_reply"), 1)

            dbt(["run", "--select", "fact_replies"], raw, db)
            self.assertEqual(count(db, "select count(*) from fact_replies"), before + 1)


if __name__ == "__main__":
    unittest.main()
