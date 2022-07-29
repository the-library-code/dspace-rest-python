import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = [
    "requests"
]

setuptools.setup(
    name="dspace-rest-client",
    version="0.1.0-dev",
    author="Kim Shepherd",
    author_email="kim@the-library-code.de",
    description="A REST API client library for DSpace 7.",
    license="BSD-3-Clause",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/the-library-code/dspace-rest-client",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    packages=["dspace_rest_client"],
    entry_points={
        "console_scripts": ["dspace-rest-client = dspace_rest_client.__main__:main"]
    },
    install_requires=install_requires,
)