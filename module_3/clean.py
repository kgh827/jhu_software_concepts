def clean_data(results):
    cleaned = []    #empty list to populate with the reformatted student record dictionaries  

    #loop through each student data record dictionary from the scrape.py file
    for item in results:
        program_name = item.get("program_name", "").strip()     #clean whitespace and hold program name for reformatting
        university   = item.get("university", "").strip()       #clean whitespace and hold university name for reformatting

        if program_name and university:                         
            program_field = f"{program_name}, {university}"     #combine them as shown in the sample json data
        elif program_name:                                      
            program_field = program_name                        
        else:                                                   
            program_field = university

        mapped = {                                              
            "program": program_field,
            "comments": item.get("notes", ""),
            "date_added": item.get("date_added", ""),
            "url": item.get("applicant_URL", ""),
            "status": item.get("applicant_status", ""),
            "term": item.get("semester", ""),
            "US/International": item.get("student_location", ""),
            "Degree": item.get("degree_title", ""),
            # CHECK: new normalized GPA/GRE fields
            "gpa": item.get("gpa") or item.get("GPA", ""),
            "gre_q": item.get("gre_q") or item.get("gre_quant") or item.get("GRE", ""),
            "gre_v": item.get("gre_v") or item.get("gre_verbal") or item.get("GRE V", ""),
            "gre_aw": item.get("gre_aw") or item.get("gre_awriting") or item.get("gre_aw_score") or item.get("GRE AW", "")
        }
        cleaned.append(mapped)                                  
    return cleaned

def save_data(cleaned):
    import json
    filename = "app_data_GRE_GPA.json"
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