"""A reply that lands after a run is picked up by the next run without a full rebuild."""
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

import duckdb

ROOT = pathlib.Path(__file__).resolve().parents[1]


def human_reply_row(replies_file):
    rows = [l for l in replies_file.read_text().splitlines() if l.split(" ")[1:2] == ["reply"]]
    return rows[-1] + "\n"


def dbt(args, raw_dir, db):
    env = dict(os.environ, GTM_TEST_DB=str(db))
    subprocess.run(
        ["uv", "run", "dbt", *args, "--target", "test", "--vars", f"{{raw_dir: '{raw_dir}'}}", "--target-path", str(db.parent / "target"), "--log-path", str(db.parent / "logs")],
        cwd=ROOT, env=env, check=True, capture_output=True, text=True,
    )


def count(db, sql):
    with duckdb.connect(str(db), read_only=True) as con:
        return con.execute(sql).fetchone()[0]


class LateReply(unittest.TestCase):
    def test_late_reply_is_captured_on_next_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = pathlib.Path(tmp) / "raw"
            shutil.copytree(ROOT / "examples" / "synthetic", raw)
            db = pathlib.Path(tmp) / "test.duckdb"
            replies = raw / "replies.txt"
            full = replies.read_text()
            late_row = human_reply_row(replies)
            replies.write_text(full.replace(late_row, ""))

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
