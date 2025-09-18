from flask import Flask, render_template, redirect, url_for, flash
from query_data import get_results              # Import to fetch analysis results
from scrape import scrape_data                  # Import scraper function
import threading                                # For background execution
from datetime import datetime                   # For timestamping refresh messages
import subprocess                               # To run the LLM as a subprocess
import os
import sys
from clean import clean_data, save_data         # Import clean.py file and relevant functions
import load_data 
from pathlib import Path

# Initialize flask application object
app = Flask(__name__)

# Setting up secret key to sign cookies securely when using the flask "flash()" functionality
app.secret_key = "secret"

# Global variable to track whether a scrape is running (this will help prevent use of the "update" button)
scrape_running = False

# Set up route for the analysis.html page. Grabs analysis results and displays them
# I recycled much of the css from my original website
@app.route("/")
def analysis():
    """
    Render the analysis page.

    This route fetches the latest analysis results from the database
    using :func:`query_data.get_results` and passes them to the
    ``analysis.html`` template for rendering.

    :return: Rendered HTML template containing analysis results.
    :rtype: str
    """
    results = get_results()  # Always fetch fresh analysis results
    return render_template("analysis.html", results=results)

# Setup for the pull_data button
@app.route("/pull_data")
def pull_data():
    """
    Trigger a background scraping and LLM processing task.

    This route starts a background thread to scrape new applicant data,
    clean it, save it to a timestamped JSON file, and then process it
    with an external LLM module. Results are later inserted into the
    database.

    A global ``scrape_running`` flag ensures that only one scrape
    runs at a time. If a scrape is already in progress, a flash
    message is displayed instead.

    :flash: Notifies the user whether a scrape is starting or already running.
    :return: Redirect to the analysis page.
    :rtype: werkzeug.wrappers.Response
    """
    global scrape_running                                                       # Global check for scrape running
    if scrape_running:                                                          # This conditional statement prevents for overlapping execution of the scraper
        flash("A scrape is already running. Please wait until it finishes.")    # Flash message to let user know there is a scrape running already
        return redirect(url_for("analysis"))                                                                              

    # Function to run the scraper file
    def run_scraper():
        """
        Internal worker function to perform scraping and LLM processing.

        - Calls :func:`scrape.scrape_data` to gather applicants.
        - Cleans results with :func:`clean.clean_data`.
        - Saves cleaned data with :func:`clean.save_data`.
        - Runs the LLM subprocess to generate JSONL output.
        - Loads LLM results into the database with :func:`load_data.main`.

        Any errors encountered during scraping or LLM execution are
        logged to stdout. ``scrape_running`` is reset to ``False`` when
        the process completes.
        """
        global scrape_running
        try:
            scrape_running = True 
            results = scrape_data(max_applicants=1000)      # Scrapes a maximum of 1000 applicants if scraping NEW data (prevents runaway scraping)
            print(f"Pulled {len(results)} new records!")

            cleaned = clean_data(results)

            # Save newly scraped data to a timestamped file
            filename = save_data(cleaned)                   

            # Attempt to run the LLM after scraping the data/creating the json
            try:
                # Resolve the current Python interpreter inside venv
                python_exe = sys.executable  

                full_path = os.path.abspath(filename)  # Absolute path to scraped JSON
                base = os.path.basename(full_path)     # e.g. scraped_20250914_115145.json
                name, _ = os.path.splitext(base)       # ("scraped_20250914_115145", ".json")
                module_3_dir = Path(__file__).resolve().parent  # Path to module_3 directory

                llm_output = os.path.join(module_3_dir, f"LLM_{name}.jsonl")

                llm_dir = Path(__file__).resolve().parent / "llm_hosting"   # Point to llm_hosting folder

                # Run the LLM and capture its stdout directly into llm_output
                with open(llm_output, "w", encoding="utf-8") as f:
                    subprocess.run(
                        [
                            python_exe, "-X", "utf8", "app.py",
                            "--file", full_path,
                            "--stdout"           # Ensures JSONL data is printed to stdout
                        ],
                        cwd=str(llm_dir),
                        stdout=f,                # Capture into LLM_scraped_*.jsonl
                        check=True
                    )

                print("LLM processing finished successfully.")
                load_data.main(llm_output)  # Load the new LLM data into the DB

            except subprocess.CalledProcessError as e:
                print(f"LLM step failed: {e}")
                return   # Stop at this point and don’t attempt to push to db

        except Exception as e:
            print(f"Error pulling data: {e}")
        finally:
            scrape_running = False

    # Run scraper in background so Flask doesn't block
    threading.Thread(target=run_scraper).start()

    # Flash notification to let the user know the scraper portion is running
    flash("Scraping + LLM processing started... you can continue using the site while it runs.")
    return redirect(url_for("analysis"))

# Routing setup for the "update analysis" button, it will only work if the scraper is NOT running.  
@app.route("/update_analysis")
def update_analysis():
    """
    Refresh the analysis page.

    This route is used to update the displayed analysis results. If a
    scrape is currently running, the update request is blocked and a
    flash message is displayed.

    Otherwise, the page is refreshed and a flash message is sent with
    the current timestamp.

    :flash: Notifies the user if analysis was refreshed or blocked by an active scrape.
    :return: Redirect to the analysis page.
    :rtype: werkzeug.wrappers.Response
    """
    if scrape_running:  # If the scraper is running, send a flash message and do not run the scraper
        flash("Cannot update analysis while scraping is in progress. Please wait.")
        return redirect(url_for("analysis"))

    # Upon completion, send flash message with timestamp of when it was updated.
    flash("Analysis refreshed at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return redirect(url_for("analysis"))

if __name__ == "__main__":  # pragma: no cover
    app.run(host="0.0.0.0", debug=True, port=8080)
