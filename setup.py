from setuptools import setup, find_packages

setup(
    name="termcast_client",
    version="0.1.0",
    description="broadcast your terminal sessions for remote viewing",
    url="https://github.com/doy/python-termcast-client",
    author="Jesse Luehrs",
    author_email="doy@tozt.net",
    license="MIT",
    classifiers=[
    ],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "termcast=termcast_client:main",
        ],
    },
)
