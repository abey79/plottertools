# `serialwrite` 

Simple tool to send the content of a file (typically HPGL) to a device with the possibility to enable HW flow control. A progress bar is displayed. In the future, the same tool will be able to send data to a remote host to which the plotter is connected (e.g. for a RPi-attached plotter).

## Use

```bash
$ serialwrite -hw my_file.hpgl /dev/tty.usb-xxxxxx
```

## Installation

Create a virtual environment for `plottertools` (if not yet done) and activate it:

```bash
$ python3 -m venv plottertools_venv
$ source plottertools_venv/bin/activate
```

Note: if you already have a virtual environment for another tools (e.g. vpype), it's ok to use it as well.

Install `serialwrite`:

```bash
$ pip install "git+https://github.com/abey79/plottertools#egg=serialwrite&subdirectory=serialwrite"
```

*Note*: mind the quotes! 
