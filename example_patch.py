# This software is licenced under the BSD 3-Clause licence
# available at https://opensource.org/licenses/BSD-3-Clause
# and described in the LICENCE file in the root of this project

"""
Example Python 3 application using the dspace.py API client library to patch
some resources in a DSpace 7 repository.
"""
from pprint import pprint

import os
import sys

from dspace_rest_client.client import DSpaceClient
from dspace_rest_client.models import Community, Collection, Item, Bundle, Bitstream

DEFAULT_URL = "https://localhost:8080/server/api"
DEFAULT_USERNAME = "username@test.system.edu"
DEFAULT_PASSWORD = "password"

# UUIDs for the object we want to patch
RESOURCE_ID = "0128787c-6f79-4661-aea4-11635d6fb04f"

# Field and value to patch
FIELD = "dc.title"
VALUE = "New title"

# Configuration from environment variables
URL = os.environ.get("DSPACE_API_ENDPOINT", DEFAULT_URL)
USERNAME = os.environ.get("DSPACE_API_USERNAME", DEFAULT_USERNAME)
PASSWORD = os.environ.get("DSPACE_API_PASSWORD", DEFAULT_PASSWORD)

# Instantiate DSpace client
d = DSpaceClient(
    api_endpoint=URL, username=USERNAME, password=PASSWORD, fake_user_agent=True
)

# Authenticate against the DSpace client
authenticated = d.authenticate()
if not authenticated:
    print("Error logging in! Giving up.")
    sys.exit(1)

# An example of searching for workflow items (any search configuration from discovery.xml can be used)
# note that the results here depend on the workflow role / access of the logged in user
search_results = d.search_objects(
    query=f"search.resourceid:{RESOURCE_ID}", dso_type="item"
)
for result in search_results:
    print(f"{result.name} ({result.uuid})")
    print(
        f"{FIELD}: {result.metadata.get(FIELD, [{'value': 'Not available'}])[0]['value']}"
    )

    item = d.get_item(uuid=result.uuid)
    print(type(item))

    if FIELD in result.metadata:
        if result.metadata[FIELD][0]["value"] == VALUE:
            print("Metadata is already correct, skipping")
            continue
        elif result.metadata[FIELD][0]["value"] != VALUE:
            patch_op = d.patch_item(
                item=item,
                operation="replace",
                field=FIELD,
                value=VALUE,
            )
            if patch_op:
                print(patch_op)
                print("Metadata updated")
            else:
                print("Error updating metadata")
    else:
        patch_op = d.patch_item(
            item=item,
            operation="add",
            field=FIELD,
            value=VALUE,
        )
        if patch_op:
            print(patch_op)
            print("Metadata added")
        else:
            print("Error adding metadata")
