"""Build the synthetic fixture in a temporary database and verify its results."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def run_demo():
    with tempfile.TemporaryDirectory(prefix="gtm-demo-") as tmp:
        db = Path(tmp) / "demo.duckdb"
        env = dict(os.environ, GTM_TEST_DB=str(db))
        command = ["uv", "run", "dbt", "build", "--target", "test",
                   "--vars", json.dumps({"raw_dir": str(ROOT / "examples/synthetic")}),
                   "--target-path", str(Path(tmp) / "target"),
                   "--log-path", str(Path(tmp) / "logs")]
        previous = None
        for _ in range(2):
            subprocess.run(command, cwd=ROOT, env=env, check=True)
            with duckdb.connect(str(db), read_only=True) as con:
                counts = con.execute("""select
                    (select count(*) from dim_lead),
                    (select count(*) from fact_sends),
                    (select count(*) from fact_sends where bounced),
                    (select count(*) from fact_replies),
                    (select count(*) from fact_replies where is_human_reply)
                """).fetchone()
                assert counts == (5, 6, 1, 2, 1), counts
                reply = con.execute("select message_type, days_to_reply from fact_replies where is_human_reply").fetchone()
                assert reply == ("pitch-c", 7), reply
                relations = con.execute("""select table_schema, table_name
                    from information_schema.tables
                    where table_schema not in ('information_schema', 'pg_catalog')
                    order by 1, 2""").fetchall()
                hashes = {}
                for schema, table in relations:
                    qualified = '"' + schema.replace('"', '""') + '"."' + table.replace('"', '""') + '"'
                    hashes[f"{schema}.{table}"] = con.execute(
                        f"select count(*), md5(coalesce(string_agg(to_json(t), '' order by to_json(t)), '')) from {qualified} t"
                    ).fetchone()
                if previous is not None:
                    assert hashes == previous, "Rows changed on the second build"
                previous = hashes
                rows = con.execute("select message_type, sends, bounced, delivered, human_replies from mart_reply_rate_by_message_type order by message_type").fetchall()
        print("\nSynthetic demo: 5 leads, 6 sends, 1 bounce, 2 inbound messages, 1 human reply.")
        print(f"Both builds match across {len(hashes)} relations.")
        print("message_type | sends | bounced | delivered | human_replies")
        for row in rows:
            print(" | ".join(map(str, row)))


if __name__ == "__main__":
    run_demo()
