#!/bin/bash

version=$1

if ! [[ $version =~ ^[0-9]+\.+[0-9]+\.[0-9]+$ ]]; then
  echo "Usage: publish.sh <version>"
  echo "Version must match the form x.y.z where all parts are numbers e.g. 0.1.13"
  exit 1
fi

echo "Building dspace_rest_client version ${version}"
if ! python setup.py bdist_wheel; then
  echo "Error: Failed to build the package"
  exit 1
fi

echo "Uploading dspace_rest_client version ${version}"
if ! twine upload --repository dspace-rest-client dist/dspace_rest_client-0.1.13-py3-none-any.whl; then
  echo "Error: Failed to upload to PyPI"
  exit 1
fi

echo "...done"
exit 0