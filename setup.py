import setuptools
import re
import os
import codecs
import sys

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open("README.md", "r", encoding="utf-8") as fh:
    LONG_DESCRIPTION = fh.read()

def read_file(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()

def find_version(*file_paths):
    try:
        version_file = read_file(*file_paths)
        version_match = re.search(r"^VERSION = ['\"]([^'\"]*)['\"]",
                                version_file, re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError("Unable to find version string.")
    except:
        return "0.0.0"

if sys.version_info < (3,):
    REQUIRES = [],
else:
    REQUIRES = ['zeroconf'],

setuptools.setup(
    name="pyShelly",
    version=find_version("pyShelly", "const.py"),
    license="MIT",
    author="StyraHem / Tarra AB",
    author_email="info@styrahem.se",
    description="Library for Shelly smart home devices",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    install_requires=REQUIRES,
    url="https://github.com/StyraHem/pyShelly",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
