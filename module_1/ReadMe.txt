Module 1 Assignment: Instructions

VERSION INFO: This site was initially built in Python 3.10, and then was finished in 3.13.7.  The site should work on anything 3.10 and higher.

1. Download the "module_1" repository from "https://github.com/kgh827/jhu_software_concepts/tree/main/module_1"

2. Open Windows Powershell, create a python environment, and activate it:
	--> For example, activating my python environment:
		PS C:\Users\Kevin> python -m venv venv
		PS C:\Users\Kevin> .\venv\Scripts\activate
	--> Your Windows Powershell window should have something resembling the following upon activating the Python environment:
		(venv) PS C:\Users\Kevin>

3. To ensure things are correctly configured, you can run a command and use the "requirements.txt" file as a reference:
		(venv) PS C:\Users\Kevin\Documents\Github\jhu_software_concepts\module_1> pip install -r requirements.txt

4. Once your python environment is active, navigate to and unzip (if necessary) the "module_1_site" folder:
	--> Once you are in the right place, your Windows Powershell should look like this:
		(venv) PS C:\Users\Kevin\Documents\Github\jhu_software_concepts\module_1\module_1_site>

5. Once at the location described in Step 4, (if everything is configured correctly), to run the site you need to run the "run.py" file in the "module_1_site" folder:
	--> The Windows Powershell command should look like this:
		(venv) PS C:\Users\Kevin\Documents\Github\jhu_software_concepts\module_1\module_1_site> python run.py
	--> Running the command above should result in Windows Powershell output similar to the following:
		 * Serving Flask app 'm1_site_app'
  		 * Debug mode: on
		 WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 		 * Running on all addresses (0.0.0.0)
 		 * Running on http://127.0.0.1:8080
 		 * Running on http://10.0.0.196:8080
		 Press CTRL+C to quit
 		 * Restarting with stat
 		 * Debugger is active!
 		 * Debugger PIN: 419-541-202

6. If everything was set up correctly, go to a web browser (i.e., Chrome, Edge, Brave, etc.) and navigate to: "http://localhost:8080/" and the site should pop up as seen in the pdf images.

7. If there are any issues setting up or running the site, please contact me at khouseh2@jh.edu

Enjoy!!

Module 1 Assignment: References

1. Module 1 Reading: https://realpython.com/flask-project/#leverage-blueprints
2. Referenced some of my old css styles from a website I built at CMU Cylab Biometrics Center

