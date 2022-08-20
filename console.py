from dspace_rest_client.client import DSpaceClient
from dspace_rest_client.models import Community, Collection, Item, Bundle, Bitstream
import code
import logging
import os

# The DSpace client will look for the same environment variables but we can also look for them here explicitly
# and as an example
url = 'http://localhost:8080/server/api'
if 'DSPACE_API_ENDPOINT' in os.environ:
    url = os.environ['DSPACE_API_ENDPOINT']
username = 'username@test.system.edu'
if 'DSPACE_API_USERNAME' in os.environ:
    username = os.environ['DSPACE_API_USERNAME']
password = 'password'
if 'DSPACE_API_PASSWORD' in os.environ:
    password = os.environ['DSPACE_API_PASSWORD']

# Instantiate DSpace client
d = DSpaceClient(api_endpoint=url, username=username, password=password)

# Authenticate against the DSpace client
authenticated = d.authenticate()
if not authenticated:
    print(f'Error logging in! Giving up.')
    exit(1)

code.interact(local=locals())
