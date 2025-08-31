from m1_site_app import create_app #imports the create_app function from "m1_site_app"

app = create_app()  #instantiates "app"

#once the "python run.py file is called in the Windows Powershell command window, this allows it to deploy on port 8080 and host 0000"
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)