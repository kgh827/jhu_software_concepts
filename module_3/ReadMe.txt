1. Name: Kevin Householder JHED ID: B91B10

2. Module 3: Databases
   Assignment Name: Database Queries
   Due Date: September 14, 2025

3. Approach:
***********IMPORTANT - The following is my assumption for the order of operations of the module 3 assignment:		
***********I have updated the scraper output to include GPA/GRE data - in module 2 I assumed these values would not be able to run through the LLM which is why I didn't include them.
***********I also reran the scraper and LLM on 30k new records in order to obtain/include the missing GPA/GRE data (LLM_app_data_GRE_GPA.json).

Pre-Requisites:
- Python 3.10
- PostgreSQL
- Installation of requirements.txt file in the module_3 folder
- .env file (for postgres)

########Instructions to Replicate What I Did:

	1. Navigate to the "module_3" folder and set up python environment: 
	--> (venv) PS C:\Users\Kevin\Documents\GitHub\module_3_Setup> py -3.10 -m venv venv 
	--> (venv) PS C:\Users\Kevin\Documents\GitHub\module_3_Setup> .\venv\Scripts\activate 
	2. From the same location, install the requirements.txt file
	--> (venv) PS C:\Users\Kevin\Documents\GitHub\module_3_Setup> pip install -r requirements.txt
	3. After ensuring Postgresql is installed and configured, run the "load_data.py" file to push the 30,000 data records (LLM_app_data_GRE_GPA.json) to the postgres database. 
	--> (venv) PS C:\Users\Kevin\Documents\GitHub\module_3_Setup> python load_data.py
	--> Output should say: "Pushed 30000 rows into applicants."
	4. To replicate the "Query_Output.pdf" image, run the "query_data.py" file as a standalone:
	--> (venv) PS C:\Users\Kevin\Documents\GitHub\module_3_Setup> python query_data.py
	--> See output in "Query_Output.pdf" image for reference of what you should see.
	5. To activate the flask app (at http://localhost:8080/):
	--> (venv) PS C:\Users\Kevin\Documents\GitHub\module_3_Setup> python app.py
	--> Site images: Flask_App_Init_p1.pdf, Flask_App_Init_p2.pdf
	6. To scrape any new records, clean them with the LLM, and push them to the existing DB, click on the "Pull Data" button and a flash warning will pop up to let you know scraping has begun.
	--> Pull Data button says: "Scraping + LLM processing started... you can continue using the site while it runs."
	--> Pressing the Update Analysis button while Pull Data is running says: "Cannot update analysis while scraping is in progress. Please wait."
	--> Pressing the Update Analysis button after Pull Data finishes says: "Analysis refreshed at 2025-09-14 13:02:59" (timestamped based on when it was updated)
	--> Images of these events: Flask_App_Pull_Data.pdf, Flask_App_Scrape_Warning.pdf, Flask_App_Updated_Analysis_p1.pdf, Flask_App_Updated_Analysis_p2.pdf

########File Descriptions:
	
	1. scrape.py
	- This file is used to scrape admissions data from the grad cafe and converts them into structured python dictionaries.
	- Applicant data is broken down into 3 rows:
		--> University, program name, degree title, date added, applicant status, decision date, and a unique applicant URL
		--> Semester, applicant location (American or International), GRE scores (Quantitative, Verbal, Analytical Writing), and GPA
		--> Notes or comments left by the applicant
	- A row checking system is implemented during scraping to determine how many rows there are per applicant (applicant data requires row 1, but not necessarily rows 2 or 3)
		--> If "tw-border-none" is not in the current row being scraped, it is row 1, otherwise it is row 2 or 3.

	- A progress counter outputs to command line for every 100 applicants scraped from the site.
	- NEW UPDATE: Before adding an applicant, it uses "url_exists_in_db(applicant_dictionary['applicant_URL']): " to determine whether an applicant already exists in the DB by referencing the applicant URL.
		--> If a duplicate URL is found, the scraper stops.
	- The data is then passed to the "clean.py" file, specifically to the "clean_data()" and "save_data" functions to standardize the json output to prepare any new data scraped for use in the LLM.

	2. clean.py
	- This file is used to clean and standardize the data from the "scrape.py" file to be processed by the LLM.
	- The clean_data() function maps fields into a consistent structure:
		--> Combines program_name and university into a single program field.
		--> Renames keys to match the expected schema (program, comments, date_added, url, status, term, US/International, Degree, gpa, gre_q, gre_v, gre_aw).
		--> Handles alternate key names (e.g., accepts both gpa and GPA, or gre_q vs GRE) to make sure all data passes through consistently.
	- The save_data() function writes the cleaned records to a timestamped JSON file to prevent overwriting prior results.
	- The load_data() function can be used to read a saved JSON file back into memory for further processing or verification.

	3. load_data.py
	- This file is used to load applicant data into the postgresql database after it has been cleaned and processed.
	- Postgresql connection credentials are in a .env file (host,port,dbname,username,password)
		--> I found that this is a best practice for security
	- A table named applicants is created (if it does not already) with the following fields:
		--> p_id: primary key
		--> program, comments, date added, url, status, term, US/International, GPA, GRE scores (Q/V/AW), degree, and LLM generated fields for program/university
	- Several functions are used to help clean/standardize data before pushing it to the database:
		--> to_date(): helps standardize date based on a variety of date formats
		--> to_float(): converts a given value to float type
		--> clean_GPA(): adds a constraint of 0.0 - 4.0 GPA scale; anything outside of that range is excluded
		--> clean_GRE(): adds a constraints of 0-6 for GRE Analytical and 130 - 170 for GRE Quantitative and Verbal scores; anything outside of those ranges are excluded
	- extract_data() maps each applicant dictionary to fit within the parameters required to be pushed to the DB without errors
		--> To avoid issues with adding additional records to existing databases, the primary key by default is based on applicant_url if available; otherwise it defaults to loop index
	- Can read json and jsonl files
	- The main function reads data that has been processed by the LLM, and if no url is provided, it defaults to "LLM_app_data_GRE_GPA.json", which allows load_data.py to also be ran asa a standalone.
		--> When ran as a standalone, it pushes all data from "LLM_app_data_GRE_GPA.json" to the table
		--> To avoid duplicates, it uses "ON_CONFLICT (p_id) DO NOTHING" to skip any duplicate applicants

	4. query_data.py
	- This file is used to query the database that has been pushed to the applicant postgresql database to be displayed by command line and the flask app.
	- The database connection also references the same .env file for the connection credentials of the db.
	- The "sql_query()" function is set up to allow for sql commands to run and returns python dictionaries, and the "pct()" function formats numbers as percentages
	- The "get_results()" function runs the series of queries for the assignment as well as the 2 additional queries created by me:
		--> Total number of applicants in the database
		--> Number of Fall 2025 applicants
		--> Percentage of international applicants
		--> Average GPA and GRE (Q/V/AW) scores
		--> Average GPA of American Fall 2025 applicants
		--> Fall 2025 acceptance rate and GPA of accepted students
		--> Number of JHU Masters in Computer Science applicants
		--> Number of Georgetown CS PhD acceptances for 2025
		--> Counts by degree type
		--> Top 10 most common universities by applicant count
	- The "url_exists_in_db()" function checks whether an applicant url exists in the database already (this is referenced by scrape.py)
	- The script can be ran as a standalone in order to check the initial data as described by step (4) above.

	5. app.py
	- This file is used to create and run the flask app that is the web interface that can be viewed at http://localhost:8080/
	- The flask app has three main routes:
		--> "/" displays the main website
		--> "/update_analysis" refreshes analysis results when new applicant data has been added
		--> "/pull_data" calls the process consisting of: scrape new data --> clean/save new data --> process using LLM --> push new data to DB
	- The /pull_data route consists of several steps:
		--> scrape_data(max_applicants=1000) function sets an upper limit of 1000 new scrapes, but can be changed as needed.
		--> New data is saved to a timestamped json file
		--> Runs LLM as a subprocess and creates a new file titled "LLM_scraped_*.json" based on the old name of the timestamped file
		--> Loads new data into the database using load_data.py
		--> Uses global "scrape_running" variable to make sure only one scrape can happen at a time
		--> Sends user progress notifications using flash alerts
	- The flask application uses threading to allow scraping/LLM processing to occur in the background while the app is not responsive.

	6. templates/analysis.html
	- This file is the flask template set up to display all data described above

	7. static/style.css
	- This is the style sheet applied to the visual display of the flask app.  I used a similar theme to my original website.

4. Development Bugs/Hangups
	- Data encoding issues are present in some of the data (for example: University of WisconsinΓÇôStout: 573)
	- Setting up the data pipeline for the "pull data" button was difficult, it was hard to get the LLM to cooperate.
	- Adjusting the reference path for the pull data button was difficult as well (where/how to save json files)
	- Had to do several iterations of the query_data sql commands to get it to work right
	- Queries for decimical and percentages were behaving strangely until implementing the "pct()" function
	- Getting the "load_data.py" and "query_data.py" files to operate as standalone as well as referenced files was difficult.
	- Getting the LLM subprocess set up and functioning took some research.  On a windows machine the command had to be very specific to get it to work.



