from setuptools import setup

with open("README.md") as f:
    readme = f.read()

with open("LICENSE") as f:
    license_file = f.read()

setup(
    name="serialwrite",
    version="0.1.0",
    description="Send a file to a local or remote serial plotter",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Antoine Beyeler",
    url="https://github.com/abey79/plottertools",
    license=license_file,
    packages=["serialwrite"],
    install_requires=[
        "click",
        "pyserial",
        "tqdm",
    ],
    entry_points="""
        [console_scripts]
        serialwrite=serialwrite.serialwrite:serialwrite
    """,
)
