import json
from datetime import datetime

def clean_data(results):
    """
    Clean and restructure scraped student records.

    :param results: Raw list of student record dictionaries from ``scrape.py``.
    :type results: list[dict]
    :return: A list of cleaned dictionaries with standardized fields.
    :rtype: list[dict]
    """
    cleaned = []    # Empty list to populate with the reformatted student record dictionaries  

    # Loop through each student data record dictionary from the scrape.py file
    for item in results:
        # Clean whitespace and hold program name/university name for reformatting
        program_name = item.get("program_name", "").strip()     
        university   = item.get("university", "").strip()       

        # Combine program and university fields as shown in the sample json data
        if program_name and university:                         
            program_field = f"{program_name}, {university}"     
        elif program_name:                                      
            program_field = program_name                        
        else:                                                   
            program_field = university

        # Restructure the student record dictionary to match the format the LLM is expecting (if everything else is in correct order, it allows gpa/gre data to pass)
        mapped = {                                              
            "program": program_field,
            "comments": item.get("notes", ""),
            "date_added": item.get("date_added", ""),
            "url": item.get("applicant_URL", ""),
            "status": item.get("applicant_status", ""),
            "term": item.get("semester", ""),
            "US/International": item.get("student_location", ""),
            "Degree": item.get("degree_title", ""),
            "gpa": item.get("gpa") or item.get("GPA", ""),     
            "gre_q": item.get("gre_q") or item.get("gre_quant") or item.get("GRE", ""),
            "gre_v": item.get("gre_v") or item.get("gre_verbal") or item.get("GRE V", ""),
            "gre_aw": item.get("gre_aw") or item.get("gre_awriting") or item.get("gre_aw_score") or item.get("GRE AW", "")
        }
        cleaned.append(mapped)                                  
    return cleaned

def save_data(cleaned):
    """
    Save cleaned student records to a JSON file.

    :param cleaned: List of cleaned student record dictionaries.
    :type cleaned: list[dict]
    :return: The filename of the saved JSON file.
    :rtype: str
    """
    # Filename is now generated based on a time stamp rather than the default file name to avoid overwriting data
    filename = f"scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Open json file to be written to and write all student dictionaries to the json file
    with open(filename, "w", encoding="utf-8") as f:            
        json.dump(cleaned, f, indent=4, ensure_ascii=False) 
    
    print(f"Student data records have been saved to:  {filename}")

    return filename

def load_data(filename):
    """
    Load student records from a JSON file.

    :param filename: Path to the JSON file containing student records.
    :type filename: str
    :return: A list of student record dictionaries.
    :rtype: list[dict]
    """
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"Student data records have been loaded from filename:  {filename}")

    #print(json.dumps(data, indent=2, ensure_ascii=False))
    return data