"""Pulls curated WordPress content out of the scratch MariaDB import as
JSON. Uses JSON_ARRAYAGG(JSON_OBJECT(...)) so MySQL itself handles all
string escaping -- far more robust than parsing the raw SQL dump by hand.

Must invoke the mariadb CLI with -r (raw mode): plain -N -B batch output
double-escapes backslashes inside the JSON text and corrupts it. The
root/root login below is the throwaway import container's own default
credentials, not a secret -- the container is local scaffolding, discarded
once extraction is done.
"""

import json
import subprocess
from pathlib import Path

CONTAINER = "egproc_mysql_import"
DATABASE = "egproc"
OUT_DIR = Path(__file__).parent / "_extracted"

QUERIES = {
    "pages.json": """
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'id', ID, 'type', post_type, 'title', post_title,
            'slug', post_name, 'date', post_date, 'content', post_content
        )) FROM egproc_posts
        WHERE post_status = 'publish' AND post_type = 'page';
    """,
    "posts.json": """
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'id', ID, 'type', post_type, 'title', post_title,
            'slug', post_name, 'date', post_date, 'content', post_content
        )) FROM egproc_posts
        WHERE post_status = 'publish' AND post_type = 'post';
    """,
    "attachments.json": """
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'id', p.ID,
            'file', (SELECT meta_value FROM egproc_postmeta pm
                     WHERE pm.post_id = p.ID AND pm.meta_key = '_wp_attached_file'
                     LIMIT 1)
        )) FROM egproc_posts p WHERE p.post_type = 'attachment';
    """,
}


def run_query(sql: str) -> list:
    full_sql = "SET SESSION group_concat_max_len = 1000000000;\n" + sql
    result = subprocess.run(
        ["docker", "exec", "-i", CONTAINER, "mariadb", "-uroot", "-proot",
         "-N", "-B", "-r", DATABASE],
        input=full_sql, capture_output=True, text=True, check=True,
    )
    raw = result.stdout.strip()
    return json.loads(raw) if raw else []


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for filename, sql in QUERIES.items():
        data = run_query(sql)
        for row in data:
            if row.get("content") is not None:
                row["content"] = row["content"].replace("\r\n", "\n")
        (OUT_DIR / filename).write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{filename}: {len(data)} rows")


if __name__ == "__main__":
    main()
