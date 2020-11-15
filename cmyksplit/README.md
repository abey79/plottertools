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

Create a virtual environment for `plottertools` (if not yet done):

```bash
$ python3 -m venv plottertools_venv
```

Activate it:

```bash
$ source plottertools_venv/bin/activate
```

Install `cmyksplit`:

```bash
$ pip install git+https://github.com/abey79/plottertools#egg=cmyksplit&subdirectory=cmyk
```
