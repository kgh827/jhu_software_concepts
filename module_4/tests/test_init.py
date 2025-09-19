import importlib
import pytest
pytestmark = pytest.mark.analysis

# Test function to validate the __init__.py file
def test_create_app():
    """
    Verify that ``src.__init__.py`` exposes a working :func:`create_app`.

    - Imports the :mod:`src` package.
    - Calls :func:`create_app` to ensure it returns a Flask application object.
    - Confirms the object is not ``None`` and has a ``name`` attribute.

    :return: None
    :rtype: NoneType
    """
    pkg = importlib.import_module("src")

    # Call the "create_app()" function
    app = pkg.create_app()

    # Verify that the app object exists
    assert app is not None

    # Verify that the app has a name
    assert getattr(app, "name", "")