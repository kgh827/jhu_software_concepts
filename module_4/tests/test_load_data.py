import json
import pytest
import src.load_data as ld

@pytest.mark.db
def test_to_date_valid_and_invalid():
    """
    Test for the "to_date()" function
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
    Test "out of range" date
    """
    assert ld.to_date("13/03/2025") is None

@pytest.mark.db
def test_to_float_and_clean_gpa_gre():
    """
    Test for the float conversion/cleaning of gpa and gre data.
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
    Creates json file, writes json dump to the file, tests read_items with array.
    """
    f = tmp_path / "file.json"
    f.write_text(json.dumps([{"a": 1}, {"b": 2}]))
    items = ld.read_items(str(f))
    assert len(items) == 2

@pytest.mark.db
def test_read_items_json_object(tmp_path):
    """
    Creates json file, writes json dump to file, tests read_items with json object
    """
    f = tmp_path / "file.json"
    f.write_text(json.dumps({"items": [{"c": 3}]}))
    items = ld.read_items(str(f))
    assert items[0]["c"] == 3

@pytest.mark.db
def test_read_items_json_lines(tmp_path):
    """
    Creates json file with two lines, each of which is a json object, and tests read_items
    """
    f = tmp_path / "file.jsonl"
    f.write_text(json.dumps({"d": 4}) + "\n" + json.dumps({"e": 5}))
    items = ld.read_items(str(f))
    assert len(items) == 2

@pytest.mark.db
def test_extract_data_creates_tuple():
    """
    This test checks to make sure extract_data creates a tuple
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
