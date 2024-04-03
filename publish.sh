#!/bin/bash
python setup.py bdist_wheel
twine upload --repository dspace-rest-client dist/dspace_rest_client-0.1.10-py3-none-any.whl