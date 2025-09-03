## STEP ONE
# First check robots.txt https://www.thegradcafe.com/robots.txt

import urllib3

########## ROBOTS.TXT FILE DATA EXTRACTION ##########

http = urllib3.PoolManager()  #set up a 'http pool manager' to make requests
url = "https://thegradcafe.com/robots.txt" #This is the url location of the robots.txt document for thegradcafe.com
response = http.request("GET", url) #Setting up a GET request to pull the contents of the robots.txt file

if response.status == 200: #IF response code 200 is detected (successful), print the robots.txt 
    text_file_output = response.data  #data provided by the response
    text_file_output = text_file_output.decode("utf-8") #decode the file into a more readable format (utf-8 is plain text/.txt)
    print('Robots.txt file loaded successfully.')
    #print(text_file_output) #print resulting text
else:
    print('There was an issue with the url entered.')

########## BEGIN ADMISSIONS DATA EXTRACTION ##########
## Going to need to initially set up pulling the first page of results
# need to extract <tr></tr>
# when examining, the first row of data is <tr></tr>, <tr class="tw-border-none"> for the second and third possible rows
## Then need to enact the "submit form" type of action shown in the readings (cant remember if reading 1 or 2)

import urllib3
from bs4 import BeautifulSoup

http = urllib3.PoolManager()  #set up a 'http pool manager' to make requests

url = "https://www.thegradcafe.com/survey/" #Initial start page for pulling

response = http.request("GET", url)

if response.status == 200: #IF response code 200 is detected
    soup = BeautifulSoup(response.data, "html.parser")
    results = soup.find("table")
    data_rows = results.find_all("tr")
    data_row_cards = [tr for tr in data_rows]

    #categories = ['School','']

    for data_row in data_row_cards:
        cells = data_row.find_all(["td", "th"])
        if not cells:
            continue  # skip empty rows
        print(" | ".join(cell.get_text(strip=True) for cell in cells))
else:
    print('There was an issue with the url entered.')