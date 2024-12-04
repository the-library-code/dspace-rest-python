# This software is licenced under the BSD 3-Clause licence
# available at https://opensource.org/licenses/BSD-3-Clause
# and described in the LICENCE file in the root of this project

"""
Example Python 3 application using the dspace.py API client library to create
some resources in a DSpace 7 repository.
"""
from pprint import pprint

import os
import sys

from dspace_rest_client.client import DSpaceClient
from dspace_rest_client.models import Community, Collection, Item, Bundle, Bitstream

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
# DSpace-Python-REST-Client/x.y.z
# To specify a custom user agent, set the USER_AGENT env variable and leave/set
# fake_user_agent as False
d = DSpaceClient(api_endpoint=URL, username=USERNAME, password=PASSWORD, fake_user_agent=True)

# Authenticate against the DSpace client
authenticated = d.authenticate()
if not authenticated:
    print('Error logging in! Giving up.')
    sys.exit(1)

# Put together some basic Community data.
# See https://github.com/DSpace/RestContract/blob/main/communities.md
community_data = {
    'name': 'Community created by the Python REST Client',
    'metadata': {
        'dc.title': [
            {'value': 'Community created by the Python REST Client',
             'language': 'en', 'authority': None, 'confidence': -1
             },
            {'value': 'Vom Python-REST-Client erstellte Community',
             'language': 'de', 'authority': None, 'confidence': -1
             }
        ]
    }
}

# Create the new community
# In this example, we'll just make this a top-level community by
# passing None as the parent parameter
COMMUNITY_PARENT = None
new_community = d.create_community(parent=COMMUNITY_PARENT, data=community_data)
if isinstance(new_community, Community) and new_community.uuid is not None:
    print(f'New community created! Handle: {new_community.handle}')
else:
    print('Error! Giving up.')
    sys.exit(1)

# Update the community metadata
new_community.name = 'Community created by the Python REST Client - Updated Name'
new_community.metadata['dc.title'][0] = {
    'value': 'Community created by the Python REST Client - Updated Name',
    'language': 'en', 'authority': None, 'confidence': -1
}

# Linked resources can be embedded with responses, e.g.
updated_community = d.update_dso(new_community, embeds=['logo', 'collections'])
# Print logo (it'll be None in this case, but just an example
print(f"Logo for updated community is {updated_community.embedded['logo']}")

# Put together some basic Collection data.
# See https://github.com/DSpace/RestContract/blob/main/collections.md
collection_data = {
    'name': 'Collection created by the Python REST Client',
    'metadata': {
        'dc.title': [
            {'value': 'Collection created by the Python REST Client',
             'language': 'en', 'authority': None, 'confidence': -1
             },
            {'value': 'Vom Python-REST-Client erstellte Sammlung',
             'language': 'de', 'authority': None, 'confidence': -1
             }
        ]
    }
}

# Create the new collection
# In this example, we'll pass the new community UUID as our parent container
collection_parent = new_community.uuid
new_collection = d.create_collection(parent=collection_parent, data=collection_data)
if isinstance(new_collection, Collection) and new_collection.uuid is not None:
    print(f'New collection created! Handle: {new_collection.handle}')
else:
    print('Error! Giving up.')
    sys.exit(1)

# Put together some basic Item data.
# (See: https://github.com/DSpace/RestContract/blob/main/items.md)
item_data = {
    "name": "Test Item created by the Python REST Client",
    "metadata": {
        "dc.contributor.author": [
            {
                "value": "Shepherd, Kim",
                "language": "en",
                "authority": None,
                "confidence": -1
            }
        ],
        "dc.title": [
            {
                "value": "Test Item created by the Python REST Client",
                "language": "en",
                "authority": None,
                "confidence": -1
            }
        ],
        "dc.type": [
            {
                "value": "Journal Article",
                "language": "en",
                "authority": None,
                "confidence": -1
            }
        ]
    },
    "inArchive": True,
    "discoverable": True,
    "withdrawn": False,
    "type": "item"
}

# The creation process for an item is a bit different, because they're typically a bit more
# complex than a container object. However, they're all DSOs at the end of the day so we
# could make usage fully consistent if we wanted.
#
# Instantiate an empty Item, passing the full API resource data to the constructor.
item = Item(item_data)

# Create the item using the new collection as the parent container.
# Note that we're passing the full Item object here, not just the dict data
# (though it will be serialised to a dict before the final POST)
new_item = d.create_item(parent=new_collection.uuid, item=item)
if isinstance(new_item, Item) and new_item.uuid is not None:
    print(f'New item created! Handle: {new_item.handle}')
else:
    print('Error! Giving up.')
    sys.exit(1)

# Add a single metadata field+value to the item (PATCH operation)
updated_item = d.add_metadata(dso=new_item, field='dc.description.abstract',
                              value='Added abstract to an existing item',
                              language='en', authority=None, confidence=-1)

# Create a new ORIGINAL bundle
# See https://github.com/DSpace/RestContract/blob/main/bundles.md
new_bundle = d.create_bundle(parent=new_item, name='ORIGINAL')
if isinstance(new_bundle, Bundle) and new_bundle.uuid is not None:
    print(f'New bundle created! UUID: {new_bundle.uuid}')
else:
    print('Error! Giving up.')
    sys.exit(1)

# Create and upload a new bitstream using the LICENSE.txt file in this project
# Set bitstream metadata
# See https://github.com/DSpace/RestContract/blob/main/bitstreams.md
bitstream_metadata = {
    'dc.description':
        [{"value": "Bitstream uploaded by Python REST Client", 'language': 'en',
          'authority': None, 'confidence': -1, 'place': 0}]
}

# Set the mime type (using mimetypes.guess_type is recommended for real uploads if you
# don't want to set manually)
FILE_MIME = 'text/plain'
# Set a better file name for our test upload
FILE_NAME = 'uploaded_file.txt'
# Create the bitstream and upload the file
new_bitstream = d.create_bitstream(bundle=new_bundle, name=FILE_NAME,
                                   path='LICENSE.txt', mime=FILE_MIME, metadata=bitstream_metadata)
if isinstance(new_bitstream, Bitstream) and new_bitstream.uuid is not None:
    print(f'New bitstream created! UUID: {new_bitstream.uuid}')
else:
    print('Error! Giving up.')
    sys.exit(1)

print('All finished with example data creation. Visit your test repository to review \
    created objects')

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
        # Get all items in this collection - see that the recommended method is a search,
        # scoped to this collection
        # (there is no collection/items endpoint, though there is a /mappedItems endpoint,
        # not yet implemented here)
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
                    if r is not None and r.headers is not None:
                        print(
                            '\tHeaders (server info, not calculated locally)\n'
                            f'\tmd5: {r.headers.get("ETag")}\n'
                            f'\tformat: {r.headers.get("Content-Type")}\n'
                            f'\tlength: {r.headers.get("Content-Length")}\n'
                            f'\tLOCAL LEN(): {len(r.content)}'
                        )
                    # Uncomment the below to get the binary data in content and then do
                    # something with it like print, or write to file, etc. You want to use
                    # the 'content' property of the response object
                    #
                    # print(r.content)

# Finally, let's show the new _iter methods which will transparently handle pagination
# and return iterators which you can use as normal
for i, search_result in enumerate(d.search_objects_iter('*:*')):
    print(f'Result #{i}: {search_result.name} ({search_result.uuid})')
