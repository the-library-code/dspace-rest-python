from dspace import DSpaceClient, Item, Community, Collection, Bundle, Bitstream
import code

url = 'http://localhost:8080/server/api'
username = 'username@test.system.edu'
password = 'password'

# Instantiate DSpace client
d = DSpaceClient(api_endpoint=url, username=username, password=password)

# Authenticate against the DSpace client
authenticated = d.authenticate()
if not authenticated:
    print(f'Error logging in! Giving up.')
    exit(1)

code.interact(local=locals())
