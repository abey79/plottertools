from setuptools import setup

with open("README.md") as f:
    readme = f.read()

with open("LICENSE") as f:
    license_file = f.read()

setup(
    name="raxicli",
    version="0.1.0",
    description="Split an image in CMYK layers",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Antoine Beyeler",
    url="https://github.com/abey79/plottertools",
    license=license_file,
    packages=["raxicli"],
    install_requires=["fabric", "toml"],
    entry_points="""
        [console_scripts]
        raxicli=raxicli.raxicli:main
    """,
)
