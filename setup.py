import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyShelly-styrahem",
    version="0.0.1",
    author="Håkan Åkerberg",
    author_email="hakan@tarra.se",
    description="A Python library for Shelly smart home devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/StyraHem/pyShelly",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
