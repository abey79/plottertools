import os

import click
import numpy as np
from PIL import Image, ImageOps


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--invert", "-i", is_flag=True, help="invert the layers before saving")
def cmyksplit(path, invert):
    """Load image at PATH, convert it to CMYK, optionally invert the result and save layers
    as individual image files."""
    path_prefix, ext = os.path.splitext(path)

    im = np.array(Image.open(path).convert("CMYK"))

    # generate black layer
    min_cmy = np.min(im[..., 0:3], axis=2)
    for i in range(3):
        im[:, :, i] = (im[:, :, i] - min_cmy) / (1 - min_cmy / 255)
    im[:, :, 3] = min_cmy

    for i, layer_name in enumerate(["cyan", "magenta", "yellow", "black"]):
        img = Image.fromarray(im[:, :, i])
        if invert:
            img = ImageOps.invert(img)
        img.save(path_prefix + "_" + layer_name + ext)
