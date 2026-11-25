"""`python -m konis.alerts_cli summary.json`: raise GitHub issue alerts from a run summary."""

import json
import os
import sys

from konis.alerts import raise_alerts

if __name__ == "__main__":
    with open(sys.argv[1]) as fh:
        s = json.load(fh)
    url = (f"{os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}"
           f"/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}")
    for a in raise_alerts(s["sources"], s["run_id"], url):
        print("alert:", a)
