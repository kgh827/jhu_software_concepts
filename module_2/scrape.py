def scrape_data(max_applicants):
    ########## BEGIN ADMISSIONS DATA EXTRACTION ##########
    ## Going to need to initially set up pulling the first page of results
    # need to extract <tr></tr>
    # when examining, the first row of data is <tr></tr>, <tr class="tw-border-none"> for the second and third possible rows
    ## Then need to enact the "submit form" type of action shown in the readings

    import urllib3
    from bs4 import BeautifulSoup
    import time


    all_applicants = []         #this will eventually hold all of the applicant dictionaries to be sent to json
    #max_applicants = 100      #number of students data to scrape

    http = urllib3.PoolManager()                        #set up a 'http pool manager' to make requests

    initial_url = "https://www.thegradcafe.com/survey/" #Initial start page for pulling
    page = 1                                            #page number counter


    while len(all_applicants) < max_applicants:
        #print(f"Scraping page {page}... (currently {len(all_applicants)} applicants)")
        #print(f"Currently on {len(all_applicants)}")
        url = f"{initial_url}?page={page}" if page > 1 else initial_url     #iterates through current url
        response = http.request("GET", url)

        soup = BeautifulSoup(response.data, "html.parser")  #instantiate beautifulsoup html parser
        results = soup.find("table")                        #using beautifulsoup to find the first table in the document

        data_rows = results.find_all("tr")                  #using beautifulsoup to find <tr> table rows which is where the relevant data is  
        data_row_list = []                                  #list of all table rows appended together for this page
        for tr in data_rows:
            data_row_list.append(tr)

        #Categories of data to be extracted from the site
        #for the URL, it is when you click on the little '...' thing on the right
        #some of these need to be handled differently depending on their "depth" in the html tags
        # r1_categories = ['university','program_name','degree_title','date_added','applicant_status','decision_date','applicant_URL']
        # r2_categories = ['semester','student_location','GRE','GRE V','GRE AW','GPA']
        # r3_categories = ['notes']

        row_check = 0   #this variable acts as a reference to tell how many rows of data there are when parsing through

        for data_row in data_row_list:

            has_header = data_row.find("th") is not None    #identifies list of header cells
            has_data   = data_row.find("td") is not None    #identifies list of data cells 
            if has_header or not has_data:                  #if the row is a header, or if it doesn't have data, skip to the next row/loop iteration                
                continue   

            row_classes = data_row.get("class") or []       #this grabs the <tr> classes (or not) which allows to identify 2nd, 3rd rows

            data_entries = []                               #empty list to populate with data rows

            for td in data_row.find_all("td"):                  #loop through the data cells 
                sub_items = td.find_all(["span", "div"])        # If the data cell has multiple child spans/divs, extract each one separately
                if sub_items:
                    for sub in sub_items:                       # iterates through the sub items to extract additional data
                        text = sub.get_text(" ", strip=True)    #splits text entries based on the "  " whitespace

                        if text:                                # further split if multiple fields are jammed together
                            parts = text.split("  ")            #splits text entries based on the "  " whitespace
                            for part in parts:              
                                if part.strip():                        #strips whitespace from text
                                    data_entries.append(part.strip())
                else:                                                   #this else is for when there is no additional span with nested data
                    text = td.get_text(" ", strip=True)                 #splits text entries based on the "  " whitespace
                    if text:
                        parts = text.split("  ")                        #splits text entries based on the "  " whitespace
                        for part in parts:
                            if part.strip():                            #strips whitespace from text
                                data_entries.append(part.strip())

            # row one data entry default values
            university = ""
            program_name = ""
            degree_title = ""
            date_added = ""
            applicant_status = ""
            decision_date = ""
            applicant_URL = ""

            #row two data entry default values
            semester = ""
            student_location = ""
            GRE = ""
            GRE_V = ""
            GRE_AW = ""
            GPA = ""

            #row three data entry default values
            notes = ""

            if "tw-border-none" not in row_classes:                                                 # Row 1 of data has no class (haha), Row 2 and 3 have 'tw-border-none'

                if row_check != 0:                                                                  # if row_check is greater than zero, append to dictionary
                    if applicant_dictionary["university"] or applicant_dictionary["program_name"]:  #used these bc these fields are almost always present/good indicator
                        all_applicants.append(applicant_dictionary)                                 #add applicant data record to the dictionary
                        if len(all_applicants) >= max_applicants:                                   #check to see if we have reached the desired number of applicant records
                            print(f"Reached limit of {max_applicants} applicants")
                            return all_applicants                                                   #if we hit this point, exit the function early
                
                #Blank dictionary to populate for each applicant.  Each row is initially defined as default empty in case data is missing
                applicant_dictionary = {
                    # Row 1 data
                    "university": "",
                    "program_name": "",
                    "degree_title": "",
                    "date_added": "",
                    "applicant_status": "",
                    "decision_date": "",
                    "applicant_URL": "",
                    # Row 2 data
                    "semester": "",
                    "student_location": "",
                    "GRE": "",
                    "GRE V": "",
                    "GRE AW": "",
                    "GPA": "",
                    # Row 3 data
                    "notes": ""
                }  
                
                tds = data_row.find_all("td")                                                                       #find all data cells for this row of data

                applicant_dictionary['university'] = tds[0].get_text(" ", strip=True) if len(tds) > 0 else ""      #add university to applicant_dictionary

                #program name and degree title are usually nested/grouped together, need to split them up
                program_name = ""
                degree_title = ""
                if len(tds) > 1:
                    spans = tds[1].find_all("span")                         #find span where progrm name and degree title are located
                    if len(spans) >= 1:                                     # if the span contains more than 0 entries, use it as program name
                        program_name = spans[0].get_text(" ", strip=True)   # strip whitespace and store program_name
                    if len(spans) >= 2:                                     #if span contains more than 1 entry, use this as degree_title
                        degree_title = spans[1].get_text(" ", strip=True)   #strip whitespace and store degree_title

                applicant_dictionary['program_name'] = program_name         #add program_name to applicant_dictionary
                applicant_dictionary['degree_title'] = degree_title         #add degree_title to applicant_dictionary

                # Date added to site
                applicant_dictionary['date_added'] = tds[2].get_text(" ", strip=True) if len(tds) > 2 else ""   #add date_added to applicant_dictionary

                # Split up applicant status and decision date
                applicant_status = ""
                decision_date = ""

                if len(tds) > 3:                                                            #checking to make sure there is still additional data to scrape
                    decision_text = tds[3].get_text(" ", strip=True)                        #set up and extract decision variable

                    bad_data = ["Total comments", "Open options", "See More", "Report"]     #set this up to eliminate "bad data" aka unnecessary text
                    for item in bad_data:
                        decision_text = decision_text.replace(item, "").strip()             #replaces the bad data item with "" --> replaces with nothing

                    if " on " in decision_text:                                             #checking to see if data is formatted how we want (contains "on")
                        parts = decision_text.split(" on ", 1)                              #Using the word "on", split the text into status/decision date
                        applicant_status = parts[0].strip()                                 #scrape/extract applicant_status
                        decision_date = parts[1].strip()                                    #scrape/extract decision_date
                    else:
                        applicant_status = decision_text.strip()                            #default to full data cell

                applicant_dictionary['applicant_status'] = applicant_status                 #add applicant_status to applicant_dictionary
                applicant_dictionary['decision_date'] = decision_date                       #add decision_date to applicant_dictionary
                
                url_tag = data_row.find("a", href=True, attrs={"data-ext-page-id": True})                           #searches for the applicant link in the by using several identifiers
                applicant_dictionary['applicant_URL'] = url_tag["href"].split("#")[0] if url_tag else ""            #add applicant_url to applicant_dictionary

                # print("Row 1 Data:")
                # print("  University:", university)
                # print("  Program_Name:", program_name)
                # print("  Degree_Title:", degree_title)
                # print("  Date_Added:", date_added)
                # print("  Applicant_Status:", applicant_status)
                # print("  Decision_Date:", decision_date)
                # print("  URL:", applicant_URL)

                row_check = 1

            elif row_check == 1:
                #if there is a row 2, break row 2 entries into variables
                semester = ""
                student_location = ""
                GRE = ""
                GRE_V = ""
                GRE_AW = ""
                GPA = ""

                if data_row.find("td"):                                 #checks to see if there is any data cells in row 2
                    row2_td = data_row.find("td")                       #extracts the data cells for row 2

                    row2_parts = []                                     #empty list for row 2 data
                    for part in row2_td.find_all(["span", "div"]):      #searching for span or div elements that may contain additional data
                        
                        text_val = part.get_text(" ", strip=True)       #extracts text and eliminates white space
                        if text_val:                                    # if data is stored in text_val, it gets appended t "row2_parts"
                            row2_parts.append(text_val)

                    for part in row2_parts:                                                                     # iterates through row2_parts to determine/match up data
                        if part.startswith("Fall") or part.startswith("Spring") or part.startswith("Summer"):   #determines semester based on possible options
                            applicant_dictionary['semester'] = part                                             #add semester to applicant_dictionary
                        elif "International" in part or "American" in part:                                     #determines student location based on possible options
                            applicant_dictionary['student_location'] = part                                     #add student_location to applicant_dictionary
                        elif part.startswith("GRE "):                                                           #use "GRE" as main identifier
                            if part.startswith("GRE V"):                                                        #check "GRE V" as identifier
                                applicant_dictionary['GRE V'] = part.replace("GRE V", "").strip()               #add GRE_V to applicant_dictionary
                            elif part.startswith("GRE AW"):                                                     #check "GRE AW" as identifier
                                applicant_dictionary['GRE AW'] = part.replace("GRE AW", "").strip()             #add GRE_AW to applicant_dictionary
                            else:                                                                               #otherwise
                                applicant_dictionary['GRE'] = part.replace("GRE", "").strip()                   #add GRE to applicant_dictionary
                        elif part.startswith("GPA"):                                                            #check "GPA" as identifier
                            applicant_dictionary['GPA'] = part.replace("GPA", "").strip()                       #add GPA to applicant dictionary 

                    # print("Row 2 Data:")
                    # print("  Semester:", semester)
                    # print("  Student Location:", student_location)
                    # print("  GRE:", GRE)
                    # print("  GRE V:", GRE_V)
                    # print("  GRE AW:", GRE_AW)
                    # print("  GPA:", GPA)

                    #looks forward to the next table row following the current one and grabs the next class
                    check_next_class = data_row.find_next_sibling("tr").get("class") or []    
                    if "tw-border-none" not in check_next_class:                                        #if the next class does NOT contain the class pattern for row 2 and 3
                        if applicant_dictionary["university"] or applicant_dictionary["program_name"]:  #used these bc these fields are almost always present/good indicator
                            all_applicants.append(applicant_dictionary)                                 #if it is not and the row 1 data is present, append this student data to the dictionary (because there is no row 3)
                            if len(all_applicants) >= max_applicants:                                   #same check from earlier, checks to see if we reached desired number of applicants
                                print(f"Reached limit of {max_applicants} applicants")
                                return all_applicants                                                   #exit function early if reach this point
                        row_check = 0                                                                   #reset the counter to 0 in order to start back to row 1 for the next student/iteration
                    else:
                        row_check = 2                                                                   #otherwise move to row 3
                
                # row_check = 2

            elif row_check == 2:
                #If there is a row 3, break row 3 into the notes section
                applicant_dictionary['notes'] = data_entries[0] if len(data_entries) > 0 else ""    #add notes to applicant dictionary
                # print("Row 3 data:")
                # print("  Notes:", notes)
                if applicant_dictionary["university"] or applicant_dictionary["program_name"]:      #used these bc these fields are almost always present/good indicator
                    all_applicants.append(applicant_dictionary)
                    if len(all_applicants) >= max_applicants:                                       #same check as previous two, checks to see if we reached desired number of applicants
                        print(f"Reached limit of {max_applicants} applicants")
                        return all_applicants                                                       #exit early if we reach desired number
                row_check = 0  # reset after finishing a listing

        if len(all_applicants) % 100 == 0:                                                          #checks remainder when dividing by 100 - this is a progress checker for command line                                                   
            print(f"Scraped {len(all_applicants)} applicants so far...", flush=True)
    
        time.sleep(0.25) #delay for smooth interaction with server

        page += 1
    print('Done scraping!')
    
    return all_applicants

if __name__ == "__main__":
    import urllib3
    ########## ROBOTS.TXT FILE DATA EXTRACTION ##########
    http = urllib3.PoolManager()                            #set up a 'http pool manager' to make requests
    url = "https://thegradcafe.com/robots.txt"              #This is the url location of the robots.txt document for thegradcafe.com
    response = http.request("GET", url)                     #Setting up a GET request to pull the contents of the robots.txt file

    if response.status == 200:                              #IF response code 200 is detected (successful), print the robots.txt 
        text_file_output = response.data                    #data provided by the response
        text_file_output = text_file_output.decode("utf-8") #decode the file into a more readable format (utf-8 is plain text/.txt)
        print('Robots.txt file loaded successfully.')
        print(text_file_output)                            #print resulting text 
    else:
        print('There was an issue with the url entered.')

    from clean import clean_data                            #importing clean_data function from clean.py
    from clean import save_data                             #importing save_data function from clean.py
    from clean import load_data                             #importing load_data function from clean.py

    max_applicants = 50                                     #user enters desired number of applicants

    results = scrape_data(max_applicants)                   #call the scrape_data(max_applicants) function to scrape data from thegradcafe                   
    print("Scraped", len(results), "records")
    cleaned = clean_data(results)                           #call the "clean_data()" function from the clean.py file
    filename = save_data(cleaned)                           #call the "save_data()" function from the clean.py file
    data = load_data(filename)                              #call the "load_data()" function from the clean.py file