import code
import os
import sys

from dspace_rest_client.client import DSpaceClient
# Import models as needed
#from dspace_rest_client.models import Community, Collection, Item, Bundle, Bitstream

DEFAULT_URL = 'http://localhost:8080/server/api'
DEFAULT_USERNAME = 'username@test.system.edu'
DEFAULT_PASSWORD = 'password'

# Configuration from environment variables
URL = os.environ.get('DSPACE_API_ENDPOINT', DEFAULT_URL)
USERNAME = os.environ.get('DSPACE_API_USERNAME', DEFAULT_USERNAME)
PASSWORD = os.environ.get('DSPACE_API_PASSWORD', DEFAULT_PASSWORD)

# Instantiate DSpace client
d = DSpaceClient(api_endpoint=URL, username=USERNAME, password=PASSWORD)

# Authenticate against the DSpace client
authenticated = d.authenticate()
if not authenticated:
    print('Error logging in! Giving up.')
    sys.exit(1)

code.interact(local=locals())
