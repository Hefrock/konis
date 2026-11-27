import json

import pytest

from konis.alerts import decide, previous_status


@pytest.mark.parametrize("ok,prev,has,expect", [
    (False, False, False, "open"),    # second failure in a row
    (False, True, False, "none"),     # first failure: wait
    (False, None, False, "none"),     # no history: wait
    (False, False, True, "none"),     # already open: no comment spam
    (True, True, True, "close"),      # second success in a row
    (True, False, True, "none"),      # first success after failure: keep open
    (True, True, False, "none"),
])
def test_decide(ok, prev, has, expect):
    assert decide(ok, prev, has) == expect


def _log(root, day, run, rows):
    d = root / day
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{run}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_previous_status_uses_latest_earlier_run(tmp_path):
    _log(tmp_path, "2026-11-26", "r1", [{"source_id": "a", "status": "stored",
                                         "fetched_at_utc": "2026-11-26T10:00:00+00:00"}])
    _log(tmp_path, "2026-11-26", "r2", [{"source_id": "a", "status": "error",
                                         "fetched_at_utc": "2026-11-26T11:00:00+00:00"},
                                        {"source_id": "b", "status": "stored",
                                         "fetched_at_utc": "2026-11-26T11:00:00+00:00"}])
    _log(tmp_path, "2026-11-26", "r3", [{"source_id": "a", "status": "stored",
                                         "fetched_at_utc": "2026-11-26T12:00:00+00:00"}])
    assert previous_status("a", "r3", tmp_path) is False   # r2 failed
    assert previous_status("a", "r4", tmp_path) is True    # r3 ok
    assert previous_status("b", "r9", tmp_path) is True
    assert previous_status("zzz", "r9", tmp_path) is None


def test_mixed_outcomes_in_one_run_count_as_failed(tmp_path):
    _log(tmp_path, "2026-11-26", "r1", [
        {"source_id": "a", "status": "stored", "fetched_at_utc": "2026-11-26T10:00:00+00:00"},
        {"source_id": "a", "status": "error", "fetched_at_utc": "2026-11-26T10:00:05+00:00"}])
    assert previous_status("a", "r2", tmp_path) is False
