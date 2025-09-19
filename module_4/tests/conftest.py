import os
import sys
import json
import time
import pytest
import builtins
import socket

# Ensure the project root is importable BEFORE touching src.*
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

@pytest.fixture(autouse=True)
def _no_dns(monkeypatch):
    # Prevent DNS resolution errors leaking into logs
    monkeypatch.setattr(
        socket, "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 0))]
    )

@pytest.fixture(autouse=True)
def _no_real_io(monkeypatch, tmp_path, request):
    """
    Global pytest fixture to prevent real file I/O and delays during tests.

    Behaviors:
      - Replaces :func:`flask_app.save_data` with a fake implementation
        that writes JSON into a temporary directory.
      - Replaces :func:`clean.save_data` with the same fake, except in the
        dedicated ``test_save_and_load_data`` test.
      - Monkeypatches ``time.sleep`` to a no-op for faster test execution.

    :param monkeypatch: Pytest fixture for patching attributes at runtime.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :param tmp_path: Temporary path provided by pytest for file writes.
    :type tmp_path: pathlib.Path
    :param request: Provides information about the requesting test function.
    :type request: _pytest.fixtures.FixtureRequest
    :yield: Applies the fixture before each test automatically.
    :rtype: None
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
