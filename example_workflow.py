# This software is licenced under the BSD 3-Clause licence
# available at https://opensource.org/licenses/BSD-3-Clause
# and described in the LICENCE file in the root of this project

"""
Example Python 3 application using the dspace.py API client library to retrieve basic DSOs in a 
DSpace repository
"""

import sys

from dspace_rest_client.client import DSpaceClient
from dspace_rest_client.models import Collection, Item, WorkspaceItem, Version
import pprint

# Import models as below if needed
# from dspace_rest_client.models import Community, Collection, Item, Bundle, Bitstream

# Example variables needed for authentication and basic API requests
# SET THESE TO MATCH YOUR TEST SYSTEM BEFORE RUNNING THE EXAMPLE SCRIPT
# You can also leave them out of the constructor and set environment variables instead:
# DSPACE_API_ENDPOINT=
# DSPACE_API_USERNAME=
# DSPACE_API_PASSWORD=
# USER_AGENT=
URL = "http://localhost:8080/server/api"
USERNAME = ""
PASSWORD = ""

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

# Start with an original item UUID, make a new version, get the new item from that, get the workspace item
# for that new item, and start workflow
original_item_uuid = '3449284d-3871-4b7a-913a-c21da13fc43f';
original_item = d.get_item(original_item_uuid)
new_version = d.create_item_version(original_item_uuid, "test", embeds=['item'])

#pprint.pprint(new_version)
if isinstance(new_version, Version):
    #pprint.pprint(new_version.as_dict())
    #pprint.pprint(new_version.embedded)
    new_version_item = Item(api_resource=new_version.embedded['item'])
    new_version_workspace_item = d.get_workspace_item(item_uuid=new_version_item.id)
    if isinstance(new_version_workspace_item, WorkspaceItem):
        workspace_item_uri = new_version_workspace_item.links['self']['href']

        # Do any extra validation here -- I ran into some testing trouble
        # because some of my archived test items happened to be missing fields
        # that were required in the submission forms/definition that I sent
        # them to...

        # If required, accept the license
        res = d.api_patch(url=workspace_item_uri,
                          operation=d.PatchOperation.ADD,
                          path="/sections/license/granted",
                          value=True,
                          params=None
                          )
        #pprint.pprint(res)
        # Start the workflow. If it has no roles you shoudl get an archived
        # item, otherwise you'll have to claim the pooled task and progress
        res = d.start_workflow(workspace_item_uri)
        pprint.pprint(res)
    


