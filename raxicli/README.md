# `raxicli` ("**r**emote **axicli**") 

This command makes it easier to run EMSL's `axicli` from a Rasberry Pi from you computer by remotely
. It's usage is exactly the same as `axicli`, but it will instead:

- if none exists, create a `screen` on the remote RPi (so you can ssh and `screen -r` if something
 goes wrong)
- for any file argument, it will `scp` the file to the remote RPi
- within the screen, call `axicli` with the provided arguments and the copied file (if any)

The bottom line is that `raxicli` with a remote axidraw is just the same as `axicli` with a local axidraw.

### Setup

`raxicli` looks for its configuration in the `~/.plottertools.toml` file. It should contain a section similar to the
 following:
 
 ```toml
[raxicli]
hostname = "axidraw.local"                           # IP/hostname of your rpi
axicli_path = "/home/pi/src/axigui/venv/bin/axicli"  # path to axicli on the rpi
svg_dir_path = "/home/pi/svg_to_plot/"               # location where the SVG should be stored on the rpi       
 ```

### Use

`raxicli` use is the exact same as `axicli`, e.g.:

```bash
$ raxicli -NT -L 2 -d 37 -u 65 -m toggle
$ raxicli -NT -L 2 -d 37 -u 65 -m plot ~/path/to/my/file.svg
$ raxicli -NT -L 2 -d 37 -u 65 -m manual -M disable_xy
```

On your RPi, you can access the screen by:

```bash
$ screen -r raxicli
```

You detach from the screen using Ctrl-A, Ctrl-D. See the [Screen User's Manual](https://www.gnu.org/software/screen/manual/screen.html) for more details.


## Installation

Create a virtual environment for `plottertools` (if not yet done) and activate it:

```bash
$ python3 -m venv plottertools_venv
$ source plottertools_venv/bin/activate
```

Note: if you already have a virtual environment for another tools (e.g. vpype), it's ok to use it as well.

Install `raxicli`:

```bash
$ pip install "git+https://github.com/abey79/plottertools#egg=raxicli&subdirectory=raxicli"
```

*Note*: mind the quotes! 
