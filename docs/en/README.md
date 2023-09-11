# Documentation

## Installation

### Setup Python Environment

```bash
pip install -r requirements/docs.txt
```

### Install Graphviz

- Windows: Download and install from [link](https://graphviz.org/download/#windows),
and add the `bin` folder to `PATH` environment variable.

- Linux: Install with `sudo apt install graphviz`,

### Install pandoc

- Windows: `conda install -c conda-forge pandoc`

- Linux: `sudo apt install pandoc`

### Build Documentation

```bash
# Windows
docs/en/make.bat html
# Linux/MacOS
docs/en/make html
```


### ~~Draw UML~~

```bash
pip install pylint
sudo apt install graphviz
pyreverse -Ak --output-directory ./docs/en/UML/ -p actor xrfeitoria.actor
pyreverse -Ak --output-directory ./docs/en/UML/ -p camera xrfeitoria.camera
pyreverse -Ak --output-directory ./docs/en/UML/ -p object xrfeitoria.object
pyreverse -Ak --output-directory ./docs/en/UML/ -p renderer xrfeitoria.renderer
pyreverse -Ak --output-directory ./docs/en/UML/ -p sequence xrfeitoria.sequence
```
