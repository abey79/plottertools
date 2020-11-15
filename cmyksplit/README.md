# cmyksplit

Command line tool to compute CMYK separation on an image and save the respective layers, optionally inverting them.

## Usage

```
Usage: cmyksplit [OPTIONS] PATH

  Load image at PATH, convert it to CMYK, optionally invert the result and
  save layers as individual image files.

Options:
  -i, --invert  invert the layers before saving
  --help        Show this message and exit.

```


## Installation

Create a virtual environment for `plottertools` (if not yet done) and activate it:

```bash
$ python3 -m venv plottertools_venv
$ source plottertools_venv/bin/activate
```

Note: if you already have a virtual environment for another tools (e.g. vpype), it's ok to use it as well.

Install `cmyksplit`:

```bash
$ pip install "git+https://github.com/abey79/plottertools#egg=cmyksplit&subdirectory=cmyksplit"
```

*Note*: mind the quotes! 
