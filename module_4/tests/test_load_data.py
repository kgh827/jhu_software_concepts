import json
import pytest
import src.load_data as ld

@pytest.mark.db
def test_to_date_valid_and_invalid():
    """
    Validate :func:`ld.to_date` with valid and invalid inputs.

    - Accepts semester terms or returns ``None``.
    - Rejects unsupported formats (e.g., YYYY-MM-DD).
    - Confirms empty strings return ``None``.

    :return: None
    :rtype: NoneType
    """
    # Semester terms expected, otherwise returns None
    assert ld.to_date("Fall 2025") is None or ld.to_date("Fall 2025") == "Fall 2025"

    # This date format is not accepted, so it should result in None
    assert ld.to_date("2025-09-01") is None

    # Empty string returns None
    assert ld.to_date("") is None

@pytest.mark.db
def test_to_date_out_of_range():
    """
    Validate :func:`ld.to_date` with out-of-range values.

    - Ensures invalid dates (e.g., month > 12) return ``None``.

    :return: None
    :rtype: NoneType
    """
    assert ld.to_date("13/03/2025") is None

@pytest.mark.db
def test_to_float_and_clean_gpa_gre():
    """
    Validate :func:`ld.to_float`, :func:`ld.clean_gpa`, and :func:`ld.clean_gre`.

    - Confirms conversion of valid floats.
    - Ensures GPA outside range (0.0–4.0) is rejected.
    - Ensures GRE values are validated by type.

    :return: None
    :rtype: NoneType
    """
    assert ld.to_float("4.0") == 4.0
    assert ld.to_float("") is None
    assert ld.clean_gpa("4.0") == 4.0
    assert ld.clean_gpa("5.0") is None
    assert ld.clean_gre("160", kind="qv") == 160
    assert ld.clean_gre("5.0", kind="aw") == 5.0

@pytest.mark.db
def test_read_items_json_list(tmp_path):
    """
    Validate :func:`ld.read_items` with a JSON array file.

    - Creates a temporary file containing a JSON list.
    - Confirms items are loaded correctly.

    :param tmp_path: Temporary file path for testing.
    :type tmp_path: pathlib.Path
    """
    f = tmp_path / "file.json"
    f.write_text(json.dumps([{"a": 1}, {"b": 2}]))
    items = ld.read_items(str(f))
    assert len(items) == 2

@pytest.mark.db
def test_read_items_json_object(tmp_path):
    """
    Validate :func:`ld.read_items` with a JSON object containing ``items``.

    - Confirms data under the ``items`` key is returned.

    :param tmp_path: Temporary file path for testing.
    :type tmp_path: pathlib.Path
    """
    f = tmp_path / "file.json"
    f.write_text(json.dumps({"items": [{"c": 3}]}))
    items = ld.read_items(str(f))
    assert items[0]["c"] == 3

@pytest.mark.db
def test_read_items_json_lines(tmp_path):
    """
    Validate :func:`ld.read_items` with JSON-lines input.

    - Confirms multiple JSON objects (one per line) are read correctly.

    :param tmp_path: Temporary file path for testing.
    :type tmp_path: pathlib.Path
    """
    f = tmp_path / "file.jsonl"
    f.write_text(json.dumps({"d": 4}) + "\n" + json.dumps({"e": 5}))
    items = ld.read_items(str(f))
    assert len(items) == 2

@pytest.mark.db
def test_extract_data_creates_tuple():
    """
    Validate :func:`ld.extract_data` produces a tuple.

    - Ensures returned tuple aligns with schema.
    - Confirms ``p_id`` and URL mapping are handled correctly.

    :return: None
    :rtype: NoneType
    """
    data = {
        "program": "CS",
        "term": "Fall 2025",
        "US/International": "International",
        "Degree": "MS",
        "gpa": "3.8",
        "gre_q": "160",
        "gre_v": "155",
        "gre_aw": "4.5",
        "url": "http://fake",
        "status": "Accepted"
    }
    result = ld.extract_data(data, idx=1)
    assert isinstance(result, tuple)
    assert result[0] == 1  # p_id
    assert result[4] == "http://fake"
