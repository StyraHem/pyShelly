import setuptools
import re
import os

here = os.path.abspath(os.path.dirname(__file__))

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyShelly",
    version="0.1.4",
    author="StyraHem / Tarra AB",
    author_email="info@styrahem.se",
    description="Library for Shelly smart home devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/StyraHem/pyShelly",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
