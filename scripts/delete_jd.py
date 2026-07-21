"""Delete a single job description (SQLite row + Qdrant chunks) from a running backend.

Runs against the live backend over HTTP and reuses the existing
``DELETE /api/v1/job-descriptions/<id>`` endpoint, which removes the Qdrant
chunks first and then the SQLite row in one atomic step.

Select the JD to delete either by its exact id or by a title substring. 
Matches are printed and you must confirm before anything is deleted.

Usage on server:
    # by exact id
    python scripts/delete_jd.py --id your_id

    # by title substring; lists matches and asks to confirm
    python scripts/delete_jd.py --title "Senior Backend"

    # list every JD without deleting anything
    python scripts/delete_jd.py --list
"""

from __future__ import annotations

import argparse
import sys

import requests


def list_jds(base_url: str) -> list[dict]:
    resp = requests.get(f"{base_url}/api/v1/job-descriptions", timeout=60)
    resp.raise_for_status()
    return resp.json()["data"]["job_descriptions"]


def _print_table(jds: list[dict]) -> None:
    for j in jds:
        print(f"  {j['id']}  {j.get('created_at', ''):<27}  {j.get('title', '')}")


def select(jds: list[dict], jd_id: str | None, title: str | None) -> list[dict]:
    if jd_id:
        return [j for j in jds if j["id"] == jd_id]
    needle = (title or "").strip().lower()
    return [j for j in jds if needle in (j.get("title") or "").lower()]


def delete(base_url: str, jd_id: str) -> None:
    resp = requests.delete(f"{base_url}/api/v1/job-descriptions/{jd_id}", timeout=60)
    resp.raise_for_status()
    print(f"Deleted JD {jd_id} (SQLite row + Qdrant chunks).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default="http://localhost:5000", help="backend base URL")
    parser.add_argument("--id", dest="jd_id", help="exact JD id (UUID) to delete")
    parser.add_argument("--title", help="case-insensitive title substring to match")
    parser.add_argument("--list", action="store_true", help="list all JDs and exit")
    parser.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = parser.parse_args()

    jds = list_jds(args.base_url)

    if args.list or (not args.jd_id and not args.title):
        if not args.list:
            print("Provide --id or --title to choose what to delete. Current job descriptions:\n")
        print(f"{len(jds)} job description(s):")
        _print_table(jds)
        return

    matches = select(jds, args.jd_id, args.title)
    if not matches:
        sys.exit("No job description matched. Run with --list to see what exists.")
    if len(matches) > 1:
        print(f"{len(matches)} job descriptions matched -- be more specific (use --id):")
        _print_table(matches)
        sys.exit(1)

    target = matches[0]
    print("About to delete this job description:")
    _print_table([target])
    if not args.yes:
        if input("Type 'yes' to confirm: ").strip().lower() != "yes":
            sys.exit("Aborted.")

    delete(args.base_url, target["id"])


if __name__ == "__main__":
    main()
