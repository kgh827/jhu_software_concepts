VERSION INFO: This was built in Python 3.10.
I am sorry this description is so wordy, but it was hard to explain easily.
The code is well commented so any other questions can likely be answered by my comments.

1. Name: Kevin Householder JHED ID: B91B10

2. Module 2: Web Scraping
   Assignment Name: Web Scraping
   Due Date: September 9, 2025

3. Approach:
***********IMPORTANT: You must run the scrape.py file as it contains the "if __name__ == "__main__":" instantiation to allow the script to run.  I have "max_applicants" set to 50 so that it can demonstratably work if tested.
***********Based on my observations and review, all components of this script function as required, and I was able to process the data using the LLM as required.
scrape.py
	
	BEGINNING: Extract robots.txt
	- When scrape.py is ran, this script initially runs the functionality to pull the "robots.txt" file from thegradcafe.
		--> Utilized the urllib3 library and I create an http pool manager: http = urllib3.PoolManager() 
		--> Targeted the location of the robots.txt site for the url: url = "https://thegradcafe.com/robots.txt" 
		--> Pulled the robots.txt file by use of a GET request: response = http.request("GET", url) 
		--> Following this I check for the status code of 200 (if it was a success) and print the contents of the file.  
		--> If it fails, the script states there was an issue  with the url.
		--> It prints out in the command line (I took the screenshot of it within vscode but i made sure it also works in powershell in a virtual environment)
	
	NEXT PORTION: scrape_data(max_applicants)
	- This portion of the code runs immediately after the robots.txt extraction.
	- Imported urllib3, beautifulsoup and time modules for use throughout this scraping portion of the script.
	- Created an empty list named "all_applicants" to be used to store all student data dictionaries scraped from the website.
	- Created a new http pool manager under the same name as before: http = urllib3.PoolManager()
	- Set the initial url to be scraped to be: initial_url = "https://www.thegradcafe.com/survey/"
	- Set a counter named "page" to equal 1 that will iterate each loop in order to "click" to the next page (i.e. to go from page 1, 2, 3, 4,...etc).
	- The main loop (while len(all_applicants) < max_applicants:) checks the length of the "all_applicants" dictionary.
	- Once in the outer while loop, I set up a dynamic url that uses the "page" counter to iterate through the pages of the site: url = f"{initial_url}?page={page}" if page > 1 else initial_url
	- Created another GET request to pull data from the current page: response = http.request("GET", url)
	- Set up the beautifulsoup html parser: soup = BeautifulSoup(response.data, "html.parser")
	- Used beautifulsoup to find the first table on the page: results = soup.find("table")
		--> My initial approach after inspecting thegradcafe.com/survey was to target the table row (<tr>) tags with my beautifulsoup4 searches.  
		--> I noticed that the initial <tr> tag had no class, and the 2nd and 3rd rows (if they exist) has a class name of "<tr class="tw-border-none">".
		--> This became the key to extracting the data found within rows 1, 2, and 3.
		--> My initial scraping script aimed to extract data from the first row of each applicant on the first page only.
	- To do this, I used beautifulsoup to extract all table rows on the first page: data_rows = results.find_all("tr")
	- I then added these to a list called "data_row_list" to be manipulated further using a for loop.
	- After this, I iterated through the data_row_list: for data_row in data_row_list:
		--> Within this for loop I performed a series of operations to separate the <span>, <td> and <div> tags into usable data.
	- Based on the data provided in the assignment prompt and the sample_data.json from the LLM, I broke the data item categories down into the ones seen in the dictionary named "applicant_dictionary".
		--> I created the structure for the "applicant_dictionary" (with default "" blank values for each field) and separated out all of the data cells and nested text for each row.
	- To extract data from the first row, "tds" extracts the data cells within the <tr> tags into a list: tds = data_row.find_all("td")
		--> tds[1] = <span> in which the "university"and "program" is nested
		--> tds[2] = date added
		--> tds[3] = applicant status & decision date; this is split using the word "on" as an identifier (i.e., "accepted ON _____").  Based on this I could extract them into separate variables
		--> To find the url tag for each applicant, I searched for an href tag: url_tag = data_row.find("a", href=True, attrs={"data-ext-page-id": True})
	- Using the same general concept as above (using "tds" to separate data rows into cells), extract data from row 2 (if row 2 exists).
	- Using the same general concept as above, extract the notes from row 3 (if row 3 exists).
	- There are a number of error checking methods throughout the script to ensure the script does not crash if data is missing (it will default to "" values).
	- To make sure the script doesn't "forget" the data from prior rows when extracting data for the 2nd and 3rd rows, the following if statements ensures the data from row 1 is still present: if applicant_dictionary["university"] or applicant_dictionary["program_name"]:
		--> This same if statement also includes a check to determine if we need to stop at the current applicant (based on the user requested input for number of applicants): if len(all_applicants) >= max_applicants: 
	- The data entries are added to the applicant_dictionary as they are being extracted throughout each row manipulation performed.
	- After completing the extraction for each applicant (depending on number of rows present), the current "applicant_data" dictionary is appended to the "all_applicants" list to be sent to the clean.py file for re-mapping.
	- Once the applicant data has been fully completed, the "all_applicants" list is returned to main: results = scrape_data(max_applicants)
		--> This data is then used as input for the clean.py file

clean.py
	- This script uses the output of the scrape.py portion of the script as input, and reformats the data to match the exact data template provided by the LLM output initially (sample_data.json).
	- Using the function clean_data(results), the data is pulled from the original dictionary (in this case it is now called "results"), and is re-structured.
		--> The data is returned in a fresh list called "cleaned" and is then sent to the "save_data(cleaned)" function.
	- The "cleaned" list of data is then sent to the "save_data(cleaned)" function which is then saved as a.json file (I have it saving to "applicant_data_CleanTest.json" so it doesn't overwrite the 30k data records if you run it).
	- The "save_data(cleaned)" function then returns the filename to be used as input to the "load_data(filename)" function.
		--> I thought about instantiating the LLM from the "load_data()" function, but I kept them as separate processes after learning how long the LLM takes to run.

4. The scrape.py file (which references the clean.py file), is able to extract 30,000 student records (or greater) from thegradcafe, and after several adjustments, the data for 30,000 students was processed by the LLM.
	- For 30,000 student records, it took roughly 30-40 minutes (on my laptop) to extract the data.
	- To process the data using the LLM provided, it took ~20 hours or so to process.  It appears that the LLM interacted successfully with the "llm-generated-program" and "llm-generated-university" fields (indicated by having valid output instead of "Unknown".

	- I experienced a number of bugs during development of the scraper,  but I managed to eliminate everything that I had encountered throughout initial testing (as far as I am aware).
	- Some of the bugs I experienced throughout development of the scraper portion of the script:
		1. Not understanding how to distinguish row 1, 2, 3
		2. Bad data in any of the fields (i.e., bad formatting)
		3. Figuring out how to get it to correctly "know" whether rows 2 and/or 3 exist, and if so, how to conditionally handle the data.
		4. Figuring out how to expand the functionality of the scraping portion to work with N number of pages and N number of applicants.
		5. I am not happy with the speed of the script overall, although I am happy it worked, but I think it may just be a slow process (and it also could be my laptop).
		6. I also needed to add in "progress tracking" functionality to let me know how many records had been scraped because it was hard to determine whether the script was actually running sometimes.

	- When using the LLM, I experienced a number of issues initially:
		1. I had to reformat my json data to fit into the format shown in the sample_data.json file because I kept getting "Unknown" in the LLM generated fields in the jsonl output.
		2. Installing the llamas package took me awhile to figure out (I am using windows, so I had to do a lot of adjustments and install the 2022 visual studio dev packages).