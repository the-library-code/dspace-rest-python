# This software is licenced under the BSD 3-Clause licence
# available at https://opensource.org/licenses/BSD-3-Clause
# and described in the LICENCE file in the root of this project

"""
Example Python 3 application using the dspace.py API client library to retrieve basic DSOs in a DSpace repository
"""

import sys

from dspace_rest_client.client import DSpaceClient
# Import models as below if needed
#from dspace_rest_client.models import Community, Collection, Item, Bundle, Bitstream

# Example variables needed for authentication and basic API requests
# SET THESE TO MATCH YOUR TEST SYSTEM BEFORE RUNNING THE EXAMPLE SCRIPT
# You can also leave them out of the constructor and set environment variables instead:
# DSPACE_API_ENDPOINT=
# DSPACE_API_USERNAME=
# DSPACE_API_PASSWORD=
# USER_AGENT=
url = 'http://localhost:8080/server/api'
username = 'username@test.system.edu'
password = 'password'

# Instantiate DSpace client
# Note the 'fake_user_agent' setting here -- this will set a string like the following, to get by Cloudfront:
# Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36
# The default is to *not* fake the user agent, and instead use the default of DSpace-Python-REST-Client/x.y.z.
# To specify a custom user agent, set the USER_AGENT env variable and leave/set fake_user_agent as False
d = DSpaceClient(api_endpoint=url, username=username, password=password, fake_user_agent=True)

# Authenticate against the DSpace client
authenticated = d.authenticate()
if not authenticated:
    print('Error logging in! Giving up.')
    sys.exit(1)

# Retrieving objects - now that we know there is some data in the repository we can demonstrate
# some simple ways of retrieving and iterating DSOs

print('\nBeginning examples of get, search methods\n')
# Get top communities
top_communities = d.get_communities(top=True)
for top_community in top_communities:
    print(f'{top_community.name} ({top_community.uuid})')
    # Get all collections in this community
    collections = d.get_collections(community=top_community)
    for collection in collections:
        print(f'{collection.name} ({collection.uuid}')
        # Get all items in this collection - see that the recommended method is a search, scoped to this collection
        # (there is no collection/items endpoint, though there is a /mappedItems endpoint, not yet implemented here)
        items = d.search_objects(query='*:*', scope=collection.uuid, dso_type='item')
        for item in items:
            print(f'{item.name} ({item.uuid})')
            # Get all bundles in this item
            bundles = d.get_bundles(parent=item)
            for bundle in bundles:
                print(f'{bundle.name} ({bundle.uuid}')
                # Get all bitstreams in this bundle
                bitstreams = d.get_bitstreams(bundle=bundle)
                for bitstream in bitstreams:
                    print(f'{bitstream.name} ({bitstream.uuid}')
                    # Download this bitstream
                    r = d.download_bitstream(bitstream.uuid)
                    print(f'\tHeaders (server info, not calculated locally)\n\tmd5: {r.headers.get("ETag")}\n'
                          f'\tformat: {r.headers.get("Content-Type")}\n\tlength: {r.headers.get("Content-Length")}\n'
                          f'\tLOCAL LEN(): {len(r.content)}')
                    # Uncomment the below to get the binary data in content and then do something with it like
                    # print, or write to file, etc. You want to use the 'content' property of the response object
                    #
                    # print(r.content)
