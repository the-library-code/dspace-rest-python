import pprint

from requests.auth import HTTPBasicAuth

from dspace_rest_client.client import DSpaceClient

URL = 'http://localhost:8080/server/api'
USERNAME = 'username@domain.com'
PASSWORD = 'password'

# To auth solr do like this and pass it as the argument in DSpaceClient
solr_auth = HTTPBasicAuth('user', 'pass')

# Instantiate DSpace client
d = DSpaceClient(api_endpoint=URL, username=USERNAME, password=PASSWORD,
                 solr_endpoint='http://localhost:8983/solr/search', solr_auth=None)

# Here's an example of a wildcard query with some filters to apply and some fields to return
results = d.solr_query('*:*',
                           filters=['search.resourcetype:Item', 'search.entitytype:*'],
                           fields=['search.resourceid', 'search.entitytype'])

for doc in results.docs:
    pprint.pprint(doc)
