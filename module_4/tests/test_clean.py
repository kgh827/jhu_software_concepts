import pytest
import json
import os
import src.clean as clean


@pytest.mark.analysis
def test_clean_data_dict_fields():
    """
    Test :func:`clean.clean_data` for correct field routing.

    - Ensures raw applicant fields are mapped into cleaned records.
    - Confirms program and university are combined.
    - Verifies GPA is preserved as a string.
    - Confirms applicant status and URL are aligned.

    :return: None
    :rtype: NoneType
    """
    # Raw applicant data that might be scraped from grad cafe
    raw = [
        {
            "program_name": "Computer Science",
            "university": "Test U",
            "notes": "Test U is a bad place",
            "date_added": "Fall 2025",
            "applicant_URL": "http://fakeurl",
            "applicant_status": "Accepted",
            "semester": "Fall 2025",
            "student_location": "International",
            "degree_title": "PhD",
            "gpa": "4.0",
            "gre_q": "165",
            "gre_v": "160",
            "gre_aw": "5.0",
        }
    ]

    # Run the clean() function
    cleaned = clean.clean_data(raw)

    # There should be 1 cleaned record
    assert len(cleaned) == 1
    first = cleaned[0]

    # Check that "program" and "university" are being combined
    assert first["program"] == "Computer Science, Test U"

    # GPA should be converted to a string
    assert first["gpa"] == "4.0"

    # Applicant status should line up accordingly
    assert first["status"] == "Accepted"

    # URL should also line up accordingly
    assert first["url"] == "http://fakeurl"


@pytest.mark.analysis
def test_clean_data_program_or_university_only():
    """
    Test :func:`clean.clean_data` with missing program or university fields.

    - If only program name is provided, it should become the ``program`` field.
    - If only university name is provided, it should become the ``program`` field.

    :return: None
    :rtype: NoneType
    """

    # Test for if only program name is provided
    raw = [{"program_name": "Math", "university": ""}]
    cleaned = clean.clean_data(raw)
    assert cleaned[0]["program"] == "Math"

    # Test for if only university name is provided
    raw = [{"program_name": "", "university": "Test U"}]
    cleaned = clean.clean_data(raw)
    assert cleaned[0]["program"] == "Test U"


@pytest.mark.analysis
def test_save_and_load_data(tmp_path):
    """
    Verify :func:`clean.save_data` and :func:`clean.load_data`.

    - ``save_data`` should write cleaned records to a JSON file.
    - ``load_data`` should successfully read them back.

    :param tmp_path: Temporary path provided by pytest for file writes.
    :type tmp_path: pathlib.Path
    :return: None
    :rtype: NoneType
    """

    # Set up a dummy cleaned data entry
    cleaned = [
        {"program": "Math", 
         "comments": "note", 
         "date_added": "2025",
         "url": "http://fake", 
         "status": "Accepted", 
         "term": "Fall",
         "US/International": "American", 
         "Degree": "MS",
         "gpa": "3.5", 
         "gre_q": "160", 
         "gre_v": "155", 
         "gre_aw": "4.5"}
    ]

    # Save data to a temporary file
    filename = clean.save_data(cleaned)
    assert os.path.exists(filename)

    # Load recently saved file
    loaded = clean.load_data(filename)
    assert isinstance(loaded, list)
    assert loaded[0]["program"] == "Math"
    assert loaded[0]["status"] == "Accepted"
