import sys

from setuptools import setup, find_packages

if len(sys.argv) > 1 and sys.argv[1] == "fatpack":
    import glob
    import io
    import zipfile

    zipdata = io.BytesIO()
    z = zipfile.ZipFile(zipdata, mode="w", compression=zipfile.ZIP_DEFLATED)
    for filename in glob.iglob("termcast_client/*.py"):
        if filename[-11:] == "__main__.py":
            arcname = "__main__.py"
        else:
            arcname = filename
        with open(filename, "rb") as f:
            z.write(filename, arcname=arcname)
    z.close()

    with open("termcast", "wb") as f:
        f.write(b"#!/usr/bin/env python\n")
        f.write(zipdata.getvalue())

    sys.exit()

setup(
    name="termcast_client",
    version="0.1.1",
    description="broadcast your terminal sessions for remote viewing",
    url="https://github.com/doy/python-termcast-client",
    author="Jesse Luehrs",
    author_email="doy@tozt.net",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Topic :: Terminals :: Terminal Emulators/X Terminals",
    ],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "termcast=termcast_client:main",
        ],
    },
)
