# tests/conftest.py
import os
import sys
import json
import time
import pytest

# Ensure the project root is importable BEFORE touching src.*
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

@pytest.fixture(autouse=True)
def _no_real_io(monkeypatch, tmp_path, request):
    """
    Prevent real file writes & program sleeps across, but allow the specific
    clean-data test to exercise the real clean.save_data.
    """

    # Fake save that actually writes JSON to tmp_path and returns the filename
    def _fake_save(data):
        p = tmp_path / "out.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return str(p)

    # Calling the fake save function to make sure flask_app.save_data isnt writing anywhere
    monkeypatch.setattr("src.flask_app.save_data", _fake_save, raising=False)

    # Calling the fake save function to make sure clean.save_data isnt writing anywhere
    if request.node.name != "test_save_and_load_data":
        monkeypatch.setattr("src.clean.save_data", _fake_save, raising=False)

    # Disables any "sleep" functions in any code to speed up testing
    monkeypatch.setattr("src.scrape.time.sleep", lambda *_: None, raising=False)
    monkeypatch.setattr(time, "sleep", lambda *_: None, raising=False)
