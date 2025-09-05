def clean_data(results):
    cleaned = []    #empty list to populate with the reformatted student record dictionaries  

    #loop through each student data record dictionary from the scrape.py file
    for item in results:
        program_name = item.get("program_name", "").strip()     #clean whitespace and hold program name for reformatting
        university   = item.get("university", "").strip()       #clean whitespace and hold university name for reformatting

        if program_name and university:                         #if program name and university name are present
            program_field = f"{program_name}, {university}"         #combine them as shown in the sample json data
        elif program_name:                                      #else if program name only exists
            program_field = program_name                        
        else:                                                   #else, default to university name only
            program_field = university

        mapped = {                                              #re-map the student record dictionary to match the format the LLM is expecting
            "program": program_field,
            "comments": item.get("notes", ""),
            "date_added": item.get("date_added", ""),
            "url": item.get("applicant_URL", ""),
            "status": item.get("applicant_status", ""),
            "term": item.get("semester", ""),
            "US/International": item.get("student_location", ""),
            "Degree": item.get("degree_title", "")
        }
        cleaned.append(mapped)                                  #append each student record dictionary to the "cleaned" list
        #print(mapped)
    return cleaned

def save_data(cleaned):
    import json
    filename = "applicant_data_filetest2.json"
    with open(filename, "w", encoding="utf-8") as f:   #open json file to be written to
        json.dump(cleaned, f, indent=4, ensure_ascii=False)  #write all student dictionaries to the json file
    
    print(f"Student data records have been saved to:  {filename}")

    return filename

def load_data(filename):
    import json
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"Student data records have been loaded from filename:  {filename}")

    #print(json.dumps(data, indent=2, ensure_ascii=False))
    return data