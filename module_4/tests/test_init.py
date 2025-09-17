import importlib

# Test function to validate the __init__.py file
def test_create_app():
    # Import the "src" folder where source code is located
    pkg = importlib.import_module("src")

    # Call the "create_app()" function
    app = pkg.create_app()

    # Verify that the app object exists
    assert app is not None

    # Verify that the app has a name
    assert getattr(app, "name", "")