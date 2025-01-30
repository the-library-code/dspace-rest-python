# This software is licenced under the BSD 3-Clause licence
# available at https://opensource.org/licenses/BSD-3-Clause
# and described in the LICENCE file in the root of this project

"""
Example Python 3 application using the dspace.py API client library to retrieve basic DSOs in a 
DSpace repository
"""

import sys
import os
from pprint import pprint

from dspace_rest_client.client import DSpaceClient

# Import models as below if needed
from dspace_rest_client.models import Community, Collection, Item, Bundle, Bitstream, DSpaceServerError

# Example variables needed for authentication and basic API requests
# SET THESE TO MATCH YOUR TEST SYSTEM BEFORE RUNNING THE EXAMPLE SCRIPT
# You can also leave them out of the constructor and set environment variables instead:
# DSPACE_API_ENDPOINT=
# DSPACE_API_USERNAME=
# DSPACE_API_PASSWORD=
# USER_AGENT=

DEFAULT_URL = 'http://localhost:8080/server/api'
DEFAULT_USERNAME = 'username@test.system.edu'
DEFAULT_PASSWORD = 'password'

# Configuration from environment variables
URL = os.environ.get('DSPACE_API_ENDPOINT', DEFAULT_URL)
USERNAME = os.environ.get('DSPACE_API_USERNAME', DEFAULT_USERNAME)
PASSWORD = os.environ.get('DSPACE_API_PASSWORD', DEFAULT_PASSWORD)
# Instantiate DSpace client
# Note the 'fake_user_agent' setting here -- this will set a string like the following,
# to get by Cloudfront:
# Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) \
# Chrome/39.0.2171.95 Safari/537.36
# The default is to *not* fake the user agent, and instead use the default of
# DSpace-Python-REST-Client/x.y.z.
# To specify a custom user agent, set the USER_AGENT env variable and leave/set
# fake_user_agent as False
d = DSpaceClient(
    api_endpoint=URL, username=USERNAME, password=PASSWORD, fake_user_agent=True
)

# Authenticate against the DSpace client
authenticated = d.authenticate()
if not authenticated:
    print("Error logging in! Giving up.")
    sys.exit(1)

# Forcing a 405 error to test (500 errors are handled too but are a bit harder to 'force' in a working system!)
try:
    r = d.fetch_resource(f"{d.API_ENDPOINT}/config/properties")
    print(r.status_code)
except DSpaceServerError as e:
    # Here you can see the formatted error message
    print("Here is a nice formatted error message:")
    print(e.format_message())
    # Here you can see a pretty print of the exception as dict, with the properties you can read
    print("\nHere is the exception as a dict:")
    pprint(e.__dict__)