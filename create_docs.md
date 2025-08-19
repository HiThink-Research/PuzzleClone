## 📖 Generating API Documentation

The project uses [Sphinx](https://www.sphinx-doc.org/en/master/) to automatically generate API documentation from the source code.

### Install Dependencies
First, install the required Python packages for building the documentation.
```
pip install sphinx sphinx-autobuild sphinx-rtd-theme
```

### Initial Setup (Run Once)
If the docs directory does not exist, initialize it with Sphinx.
```
sphinx-quickstart docs
```

### Build or Update the Documentation
To generate or refresh the HTML documentation, follow these steps:

```
cd docs
sphinx-apidoc -o source ../ "../test*" "../output*"
make clean && make html
```

### Serve the Documentation Locally
You can view the generated documentation locally using Python's built-in web server.

```
cd build/html
python -m http.server 8001
```

You can now view the documentation by navigating to http://localhost:8001 in your web browser.


### The tutorial document
You can serve the tutorial document using the following commands:

```
pip install mkdocs
cd tutorial_docs
mkdocs serve -a localhost:8002
```

The document will be available at http://localhost:8002/.
