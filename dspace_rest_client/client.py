# This software is licenced under the BSD 3-Clause licence
# available at https://opensource.org/licenses/BSD-3-Clause
# and described in the LICENSE.txt file in the root of this project

"""
DSpace REST API client library. Intended to make interacting with DSpace in Python 3 easier, particularly
when creating, updating, retrieving and deleting DSpace Objects.
This client library is a work in progress and currently only implements the most basic functionality.
It was originally created to assist with a migration of container structure, items and bistreams from a non-DSpace
system to a new DSpace 7 repository.

It needs a lot of expansion: resource policies and permissions, validation of prepared objects and responses,
better abstracting and handling of HAL-like API responses, plus just all the other endpoints and operations implemented.

@author Kim Shepherd <kim@shepherd.nz>
"""
import code
import json
import logging

import requests
from requests import Request
import os
from uuid import UUID
from models import *

__all__ = ['DSpaceClient']


def parse_json(response):
    """
    Simple static method to handle ValueError if JSON is invalid in response body
    TODO: More logging, not just console output
    @param response:
    @return:
    """
    response_json = None
    try:
        response_json = response.json()
    except ValueError as err:
        print(f'Error parsing response JSON: {err}. Body text: {response.text}')
    return response_json


class DSpaceClient:
    """
    Main class of the API client itself. This client uses request sessions to connect and authenticate to
    the REST API, maintain XSRF tokens, and all GET, POST, PUT, PATCH operations.
    Low-level api_get, api_post, api_put, api_delete, api_patch functions are defined to handle the requests and do
    retries / XSRF refreshes where necessary.
    Higher level get, create, update, partial_update (patch) functions are implemented for each DSO type
    """
    # Set up basic environment, variables
    session = None
    API_ENDPOINT = 'http://localhost:8080/server/api'
    if 'DSPACE_API_ENDPOINT' in os.environ:
        API_ENDPOINT = os.environ['DSPACE_API_ENDPOINT']
    LOGIN_URL = f'{API_ENDPOINT}/authn/login'
    USERNAME = 'username@test.system.edu'
    if 'DSPACE_API_USERNAME' in os.environ:
        USERNAME = os.environ['DSPACE_API_USERNAME']
    PASSWORD = 'password'
    if 'DSPACE_API_PASSWORD' in os.environ:
        PASSWORD = os.environ['DSPACE_API_PASSWORD']

    verbose = False

    # Simple enum for patch operation types
    class PatchOperation:
        ADD = 'add'
        REMOVE = 'remove'
        REPLACE = 'replace'
        MOVE = 'move'

    def __init__(self, api_endpoint=API_ENDPOINT, username=USERNAME, password=PASSWORD):
        """
        Accept optional API endpoint, username, password arguments using the OS environment variables as defaults
        :param api_endpoint:    base path to DSpace REST API, eg. http://localhost:8080/server/api
        :param username:        username with appropriate privileges to perform operations on REST API
        :param password:        password for the above username
        """
        self.session = requests.Session()
        self.API_ENDPOINT = api_endpoint
        self.LOGIN_URL = f'{self.API_ENDPOINT}/authn/login'
        self.USERNAME = username
        self.PASSWORD = password

    def authenticate(self):
        """
        Authenticate with the DSpace REST API. As with other operations, perform XSRF refreshes when necessary.
        After POST, check /authn/status and log success if the authenticated json property is true
        @return: response object
        """
        # Get CSRF token
        r = self.session.post(self.LOGIN_URL)
        # Look for DSPACE-XSRF-TOKEN and persist it as X-XSRF-Token in session headers
        if 'DSPACE-XSRF-TOKEN' in r.headers:
            t = r.headers['DSPACE-XSRF-TOKEN']
            print('Updating token to ' + t)
            self.session.headers.update({'X-XSRF-Token': t})
            self.session.cookies.update({'X-XSRF-Token': t})

        # POST Login
        r = self.session.post(self.LOGIN_URL, data={'user': self.USERNAME, 'password': self.PASSWORD})
        if 'Authorization' in r.headers:
            self.session.headers.update({'Authorization': r.headers.get('Authorization')})

        # Get and check authentication status
        r = self.session.get(f'{self.API_ENDPOINT}/authn/status')
        r_json = r.json()
        if 'authenticated' in r_json and r_json['authenticated'] is True:
            print(f'Authenticated successfully as {self.USERNAME}')
        else:
            return False

        return r_json['authenticated']

    def refresh_token(self):
        """
        If the DSPACE-XSRF-TOKEN appears, we need to update our local stored token and re-send our API request
        @return: None
        """
        r = self.api_post(self.LOGIN_URL, None, None)
        # Look for DSPACE-XSRF-TOKEN and persist it as X-XSRF-Token in session headers
        if 'DSPACE-XSRF-TOKEN' in r.headers:
            t = r.headers['DSPACE-XSRF-TOKEN']
            print('Updating token to ' + t)
            self.session.headers.update({'X-XSRF-Token': t})
            self.session.cookies.update({'X-XSRF-Token': t})

    def api_get(self, url, params=None, data=None):
        """
        Perform a GET request. Refresh XSRF token if necessary.
        @param url:     DSpace REST API URL
        @param params:  any parameters to include (eg ?page=0)
        @param data:    any data to supply (typically not relevant for GET)
        @return:        Response from API
        """
        r = self.session.get(url, params=params, data=data)
        if 'DSPACE-XSRF-TOKEN' in r.headers:
            t = r.headers['DSPACE-XSRF-TOKEN']
            print('Updating token to ' + t)
            self.session.headers.update({'X-XSRF-Token': t})
            self.session.cookies.update({'X-XSRF-Token': t})
        return r

    def api_post(self, url, params, json, retry=False):
        """
        Perform a POST request. Refresh XSRF token if necessary.
        POSTs are typically used to create objects.
        @param url:     DSpace REST API URL
        @param params:  Any parameters to include (eg ?parent=abbc-....)
        @param json:    Data in json-ready form (dict) to send as POST body (eg. item.as_dict())
        @param retry:   Has this method already been retried? Used if we need to refresh XSRF.
        @return:        Response from API
        """
        h = {'Content-type': 'application/json'}
        r = self.session.post(url, json=json, params=params, headers=h)
        if 'DSPACE-XSRF-TOKEN' in r.headers:
            t = r.headers['DSPACE-XSRF-TOKEN']
            print('API Post: Updating token to ' + t)
            self.session.headers.update({'X-XSRF-Token': t})
            self.session.cookies.update({'X-XSRF-Token': t})

        if r.status_code == 403:
            # 403 Forbidden
            # If we had a CSRF failure, retry the request with the updated token
            # After speaking in #dev it seems that these do need occasional refreshes but I suspect
            # it's happening too often for me, so check for accidentally triggering it
            print(r.text)
            r_json = r.json()
            if 'message' in r_json and 'CSRF token' in r_json['message']:
                if retry:
                    print('API Post: Already retried... something must be wrong')
                else:
                    print("API Post: Retrying request with updated CSRF token")
                    return self.api_post(url, params=params, json=json, retry=True)

        return r

    def api_put(self, url, params, json, retry=False):
        """
        Perform a PUT request. Refresh XSRF token if necessary.
        PUTs are typically used to update objects.
        @param url:     DSpace REST API URL
        @param params:  Any parameters to include (eg ?parent=abbc-....)
        @param json:    Data in json-ready form (dict) to send as PUT body (eg. item.as_dict())
        @param retry:   Has this method already been retried? Used if we need to refresh XSRF.
        @return:        Response from API
        """
        h = {'Content-type': 'application/json'}
        r = self.session.put(url, params=params, json=json, headers=h)
        if 'DSPACE-XSRF-TOKEN' in r.headers:
            t = r.headers['DSPACE-XSRF-TOKEN']
            print('Updating token to ' + t)
            self.session.headers.update({'X-XSRF-Token': t})
            self.session.cookies.update({'X-XSRF-Token': t})

        if r.status_code == 403:
            # 403 Forbidden
            # If we had a CSRF failure, retry the request with the updated token
            # After speaking in #dev it seems that these do need occasional refreshes but I suspect
            # it's happening too often for me, so check for accidentally triggering it
            print(r.text)
            r_json = r.json()
            if 'message' in r_json and 'CSRF token' in r_json['message']:
                if retry:
                    print('Already retried... something must be wrong')
                else:
                    print("Retrying request with updated CSRF token")
                    return self.api_put(url, params=params, json=json, retry=True)

        return r

    def api_delete(self, url, params, retry=False):
        """
        Perform a DELETE request. Refresh XSRF token if necessary.
        DELETES are typically used to update objects.
        @param url:     DSpace REST API URL
        @param params:  Any parameters to include (eg ?parent=abbc-....)
        @param retry:   Has this method already been retried? Used if we need to refresh XSRF.
        @return:        Response from API
        """
        h = {'Content-type': 'application/json'}
        r = self.session.delete(url, params=params, headers=h)
        if 'DSPACE-XSRF-TOKEN' in r.headers:
            t = r.headers['DSPACE-XSRF-TOKEN']
            print('Updating token to ' + t)
            self.session.headers.update({'X-XSRF-Token': t})
            self.session.cookies.update({'X-XSRF-Token': t})

        if r.status_code == 403:
            # 403 Forbidden
            # If we had a CSRF failure, retry the request with the updated token
            # After speaking in #dev it seems that these do need occasional refreshes but I suspect
            # it's happening too often for me, so check for accidentally triggering it
            print(r.text)
            r_json = r.json()
            if 'message' in r_json and 'CSRF token' in r_json['message']:
                if retry:
                    print('Already retried... something must be wrong')
                else:
                    print("Retrying request with updated CSRF token")
                    return self.api_delete(url, params=params, retry=True)

        return r

    def api_patch(self, url, operation, path, value, retry=False):
        """
        @param url: DSpace REST API URL
        @param operation: 'add', 'remove', 'replace', or 'move' (see PatchOperation enumeration)
        @param path: path to perform operation - eg, metadata, withdrawn, etc.
        @param value: new value for add or replace operations, or 'original' path for move operations
        @param retry:   Has this method already been retried? Used if we need to refresh XSRF.
        @return:
        @see https://github.com/DSpace/RestContract/blob/main/metadata-patch.md
        """
        if url is None:
            print(f'Missing required URL argument')
            return None
        if path is None:
            print(f'Need valid path eg. /withdrawn or /metadata/dc.title/0/language')
            return None
        if (operation == self.PatchOperation.ADD or operation == self.PatchOperation.REPLACE
                or operation == self.PatchOperation.MOVE) and value is None:
            # missing value required for add/replace/move operations
            print(f'Missing required "value" argument for add/replace/move operations')
            return None

        # compile patch data
        data = {
            "op": operation,
            "path": path
        }
        if value is not None:
            if operation == self.PatchOperation.MOVE:
                data["from"] = value
            else:
                data["value"] = value

        # set headers
        h = {'Content-type': 'application/json'}
        # perform patch request
        r = self.session.patch(url, json=[data], headers=h)
        if 'DSPACE-XSRF-TOKEN' in r.headers:
            t = r.headers['DSPACE-XSRF-TOKEN']
            print('API Post: Updating token to ' + t)
            self.session.headers.update({'X-XSRF-Token': t})
            self.session.cookies.update({'X-XSRF-Token': t})

        if r.status_code == 403:
            # 403 Forbidden
            # If we had a CSRF failure, retry the request with the updated token
            # After speaking in #dev it seems that these do need occasional refreshes but I suspect
            # it's happening too often for me, so check for accidentally triggering it
            print(r.text)
            r_json = parse_json(r)
            if 'message' in r_json and 'CSRF token' in r_json['message']:
                if retry:
                    print('Already retried... something must be wrong')
                else:
                    print("Retrying request with updated CSRF token")
                    return self.api_patch(url, operation, path, value, True)
        elif r.status_code == 200:
            # 200 Success
            print(f'successful patch update to {r.json()["type"]} {r.json()["id"]}')

        # Return the raw API response
        return r

    def search_objects(self, query=None, filters=None, dsoType=None):
        """
        Do a basic search with optional query, filters and dsoType params. TODO: pagination
        @param query:   query string
        @param filters: discovery filters as dict eg. {'f.entityType': 'Publication,equals', ... }
        @param dsoType: DSO type to further filter results
        @return:        list of DspaceObject objects constructed from API resources
        """
        dsos = []
        if filters is None:
            filters = {}
        url = f'{self.API_ENDPOINT}/discover/search/objects'
        params = filters
        if query is not None:
            params['query'] = query
        if dsoType is not None:
            params['dsoType'] = dsoType

        r_json = self.fetch_resource(url=url, params=params)

        # instead lots of 'does this key exist, etc etc' checks, just go for it and wrap in a try?
        try:
            results = r_json['_embedded']['searchResult']['_embedded']['objects']
            for result in results:
                resource = result['_embedded']['indexableObject']
                dso = DSpaceObject(resource)
                dsos.append(dso)
        except (TypeError, ValueError) as err:
            print(f'error parsing search result json {err}')

        return dsos

    def fetch_resource(self, url, params=None):
        """
        Simple function for higher-level 'get' functions to use whenever they want
        to retrieve JSON resources from the API
        @param url:     DSpace REST API URL
        @param params:  Optional params
        @return:        JSON parsed from API response or None if error
        """
        r = self.api_get(url, params, None)
        if r.status_code != 200:
            print(f'Error encountered fetching resource: {r.text}')
            return None
        # ValueError / JSON handling moved to static method
        return parse_json(r)

    def get_dso(self, url, uuid):
        """
        Base 'get DSpace Object' function.
        Uses fetch_resource which itself calls parse_json on the raw response before returning.
        @param url:     DSpace REST API URL
        @param uuid:    UUID of object to retrieve
        @return:        Parsed JSON response from fetch_resource
        """
        try:
            # Try to get UUID version to test validity
            id = UUID(uuid).version
            url = f'{url}/{uuid}'
            return self.api_get(url, None, None)
        except ValueError:
            print(f'Invalid DSO UUID: {uuid}')
            return None

    def create_dso(self, url, params, data):
        """
        Base 'create DSpace Object' function.
        Takes JSON data and some POST parameters and returns the response.
        @param url:     DSpace REST API URL
        @param params:  Any parameters to pass in the request, eg. parentCollection for a new item
        @param data:    JSON data expected by the REST API to create the new resource
        @return:        Raw API response. New DSO *could* be returned but for error checking purposes, raw response
                        is nice too and can always be parsed from this response later.
        """
        r = self.api_post(url, params, data)
        if r.status_code == 201:
            # 201 Created - success!
            new_dso = r.json()
            print(f'{new_dso["type"]} {new_dso["uuid"]} created successfully!')
        else:
            print(f'create operation failed: {r.status_code}: {r.text} ({url})')
        return r

    def update_dso(self, dso, params=None):
        """
        Update DSpaceObject. Takes a DSpaceObject and any optional parameters. Will send a PUT update to the remote
        object and return the updated object, typed correctly.
        :param dso:     DSpaceObject with locally updated data, to send in PUT request
        :param params:  Optional parameters
        :return:

        """
        if dso is None:
            return None
        dso_type = type(dso)
        if not isinstance(dso, SimpleDSpaceObject):
            print(f'Only SimpleDSpaceObject types (eg Item, Collection, Community) '
                  f'are supported by generic update_dso PUT.')
            return dso
        try:
            # Get self URI from HAL links
            url = dso.links['self']['href']
            # Get and clean data - there are some unalterable fields that could cause errors
            data = dso.as_dict()

            if 'lastModified' in data:
                data.pop('lastModified')
            """
            if 'id' in data:
                data.pop('id')
            if 'handle' in data:
                data.pop('handle')
            if 'uuid' in data:
                data.pop('uuid')
            if 'type' in data:
                data.pop('type')
            """
            r = self.api_put(url, params=params, json=data)
            if r.status_code == 200:
                # 200 OK - success!
                updated_dso = dso_type(parse_json(r))
                print(f'{updated_dso.type} {updated_dso.uuid} updated sucessfully!')
                return updated_dso
            else:
                print(f'update operation failed: {r.status_code}: {r.text} ({url})')
                return None

        except ValueError as e:
            print(f'{e}')
            return None

    def delete_dso(self, dso=None, url=None, params=None):
        """
        Delete DSpaceObject. Takes a DSpaceObject and any optional parameters. Will send a PUT update to the remote
        object and return the updated object, typed correctly.
        :param dso:     DSpaceObject from which to parse self link
        :param params:  Optional parameters
        :param url:     URI if not deleting from DSO
        :return:

        """
        if dso is None:
            if url is None:
                print(f'Need a DSO or a URL to delete')
                return None
        else:
            if not isinstance(dso, SimpleDSpaceObject):
                print(f'Only SimpleDSpaceObject types (eg Item, Collection, Community, EPerson) '
                      f'are supported by generic update_dso PUT.')
                return dso
            # Get self URI from HAL links
            url = dso.links['self']['href']

        try:
            r = self.api_delete(url, params=params)
            if r.status_code == 204:
                # 204 No Content - success!
                print(f'{url} was deleted sucessfully!')
                return r
            else:
                print(f'update operation failed: {r.status_code}: {r.text} ({url})')
                return None

        except ValueError as e:
            print(f'{e}')
            return None

    def get_bundles(self, parent=None, uuid=None):
        """
        Get bundles for an item
        @param parent:  python Item object, from which the UUID will be referenced in the URL.
                        This is mutually exclusive to the 'uuid' argument, returning all bundles for the item.
        @param uuid:    Bundle UUID. This is mutually exclusive to the 'parent' argument, returning just this bundle
        @return:        List of bundles (single UUID bundle result is wrapped in a list before returning)
        """
        # TODO: It is probably wise to allow the parent UUID to be simply passed as an alternative to having the full
        #  python object as constructed by this REST client, for more flexible usage.
        bundles = list()
        single_result = False
        if uuid is not None:
            url = f'{self.API_ENDPOINT}/core/bundles/{uuid}'
            single_result = True
        elif parent is not None:
            url = f'{self.API_ENDPOINT}/core/items/{parent.uuid}/bundles'
        else:
            return list()

        r_json = self.fetch_resource(url, params=None)
        try:
            if single_result:
                bundles.append(Bundle(r_json))
            if not single_result:
                resources = r_json['_embedded']['bundles']
                for resource in resources:
                    bundles.append(Bundle(resource))
        except ValueError as err:
            print(f'error parsing bundle results: {err}')

        return bundles

    def create_bundle(self, parent=None, name='ORIGINAL'):
        """
        Create new bundle in the specified item
        @param parent:  Parent python Item, the UUID of which will be used in the URL path
        @param name:    Name of the bundle. Default: ORIGINAL
        @return:        constructed python Bundle object from the response JSON
                        (note: this is a bit inconsistent with create_dso usage where the raw response is returned)
        """
        # TODO: It is probably wise to allow the parent UUID to be simply passed as an alternative to having the full
        #  python object as constructed by this REST client, for more flexible usage.
        if parent is None:
            return None
        url = f'{self.API_ENDPOINT}/core/items/{parent.uuid}/bundles'
        return Bundle(api_resource=parse_json(self.api_post(url, params=None, json={'name': name, 'metadata': {}})))

    def get_bitstreams(self, uuid=None, bundle=None, page=0, size=20):
        """
        Get a specific bitstream UUID, or all bitstreams for a specific bundle
        @param uuid:    UUID of a specific bitstream to retrieve
        @param bundle:  A python Bundle object to parse for bitstream links to retrieve
        @param page:    Page number, for pagination over large result sets (default: 0)
        @param size:    Size of results per page (default: 20)
        @return:        list of python Bitstream objects
        """
        url = f'{self.API_ENDPOINT}/core/bitstreams/{uuid}'
        if uuid is None and bundle is None:
            return list()
        if uuid is None and isinstance(bundle, Bundle):
            if 'bitstreams' in bundle.links:
                url = bundle.links['bitstreams']['href']
            else:
                url = f'{self.API_ENDPOINT}/core/bundles/{bundle.uuid}/bitstreams'
                print(f'Cannot find bundle bitstream links, will try to construct manually: {url}')
        # Perform the actual request. By now, our URL and parameter should be properly set
        r_json = self.fetch_resource(url, params={'page': page, 'size': size})
        if '_embedded' in r_json:
            if 'bitstreams' in r_json['_embedded']:
                bitstreams = list()
                for bitstream_resource in r_json['_embedded']['bitstreams']:
                    bitstreams.append(Bitstream(bitstream_resource))
                return bitstreams

    def create_bitstream(self, bundle=None, name=None, path=None, mime=None, metadata=None, retry=False):
        """
        Upload a file and create a bitstream for a specified parent bundle, from the uploaded file and
        the supplied metadata.
        This create method is a bit different to the others, it does not use create_dso or the api_post lower level
        methods, instead it has to use a prepared session POST request which will allow the multi-part upload to work
        successfully with the correct byte size and persist the session data.
        This is also why it directly implements the 'retry' functionality instead of relying on api_post.
        @param bundle:      python Bundle object
        @param name:        Bitstream name
        @param path:        Local filesystem path to the file that will be uploaded
        @param mime:        MIME string of the uploaded file
        @param metadata:    Full metadata JSON
        @param retry:       A 'retried' indicator. If the first attempt fails due to an expired or missing auth
                            token, the request will retry once, after the token is refreshed. (default: False)
        @return:            constructed Bitstream object from the API response, or None if the operation failed.
        """
        # TODO: It is probably wise to allow the bundle UUID to be simply passed as an alternative to having the full
        #  python object as constructed by this REST client, for more flexible usage.
        # TODO: Better error detection and handling for file reading
        if metadata is None:
            metadata = {}
        url = f'{self.API_ENDPOINT}/core/bundles/{bundle.uuid}/bitstreams'
        file = (name, open(path, 'rb'), mime)
        files = {'file': file}
        properties = {'name': name, 'metadata': metadata, 'bundleName': bundle.name}
        payload = {'properties': json.dumps(properties) + ';application/json'}
        h = self.session.headers
        h.update({'Content-Encoding': 'gzip'})
        req = Request('POST', url, data=payload, headers=h, files=files)
        prepared_req = self.session.prepare_request(req)
        r = self.session.send(prepared_req)
        if 'DSPACE-XSRF-TOKEN' in r.headers:
            t = r.headers['DSPACE-XSRF-TOKEN']
            print('Updating token to ' + t)
            self.session.headers.update({'X-XSRF-Token': t})
            self.session.cookies.update({'X-XSRF-Token': t})
        if r.status_code == 403:
            r_json = r.json()
            if 'message' in r_json and 'CSRF token' in r_json['message']:
                if retry:
                    print('Already retried... something must be wrong')
                else:
                    print("Retrying request with updated CSRF token")
                    return self.create_bitstream(bundle, name, path, mime, metadata, True)

        if r.status_code == 201 or r.status_code == 200:
            # Success
            return Bitstream(api_resource=parse_json(r))
        else:
            print(f'Error creating bitstream: {r.status_code}: {r.text}')
            return None

    def get_communities(self, uuid=None, page=0, size=20, top=False):
        """
        Get communities - either all, for single UUID, or all top-level (ie no sub-communities)
        @param uuid:    string UUID if getting single community
        @param page:    integer page (default: 0)
        @param size:    integer size (default: 20)
        @param top:     whether to restrict search to top communities (default: false)
        @return:        list of communities, or None if error
        """
        url = f'{self.API_ENDPOINT}/core/communities'
        params = {'page': page, 'size': size}
        if uuid is not None:
            try:
                # This isn't used, but it'll throw a ValueError if not a valid UUID
                id = UUID(uuid).version
                # Set URL and parameters
                url = f'{url}/{uuid}'
                params = None
            except ValueError:
                print(f'Invalid community UUID: {uuid}')
                return None

        if top:
            # Set new URL
            url = f'{url}/search/top'

        print(f'Performing get on {url}')
        # Perform actual get
        r_json = self.fetch_resource(url, params)
        if '_embedded' in r_json:
            if 'communities' in r_json['_embedded']:
                communities = list()
                for community_resource in r_json['_embedded']['communities']:
                    communities.append(Community(community_resource))
                return communities

        # Default return of empty list
        return list()

    def create_community(self, parent, data):
        """
        Create a community, either top-level or beneath a given parent
        @param parent:  (optional) parent UUID to pass as a parameter to create_dso
        @param data:    Full JSON data for the new community
        @return:        python Community object constructed from the API response
        """
        # TODO: To be consistent with other create methods, this should probably also allow a Community object
        #  to be passed instead of just the UUID as a string
        url = f'{self.API_ENDPOINT}/core/communities'
        params = None
        if parent is not None:
            params = {'parent': parent}
        return Community(api_resource=parse_json(self.create_dso(url, params, data)))

    def get_collections(self, uuid=None, community=None, page=0, size=20):
        """
        Get collections - all, or single UUID, or for a specific community
        @param uuid:        UUID string. If present, just a single collection is returned (overrides community arg)
        @param community:   Community object. If present (and no uuid present), collections for a community
        @param page:        Integer for page / offset of results. Default: 0
        @param size:        Integer for page size. Default: 20 (same as REST API default)
        @return:            list of Collection objects, or None if there was an error
                            for consistency of handling results, even the uuid search will be a list of one
        """
        url = f'{self.API_ENDPOINT}/core/collections'
        params = {'page': page, 'size': size}
        # First, handle case of UUID. It overrides the other arguments as it is a request for a single collection
        if uuid is not None:
            try:
                id = UUID(uuid).version
                # Update URL and parameters
                url = f'{url}/{uuid}'
                params = None
            except ValueError:
                print(f'Invalid collection UUID: {uuid}')
                return None

        if community is not None:
            if 'collections' in community.links and 'href' in community.links['collections']:
                # Update URL
                url = community.links['collections']['href']

        # Perform the actual request. By now, our URL and parameter should be properly set
        r_json = self.fetch_resource(url, params=params)
        if '_embedded' in r_json:
            if 'collections' in r_json['_embedded']:
                collections = list()
                for collection_resource in r_json['_embedded']['collections']:
                    collections.append(Collection(collection_resource))
                return collections

        return list()

    def create_collection(self, parent, data):
        """
        Create collection beneath a given parent community.
        @param parent:  UUID of parent community to pass as a parameter to create_dso
        @param data:    Full JSON data for the new collection
        @return:        python Collection object constructed from the API response
        """
        # TODO: To be consistent with other create methods, this should probably also allow a Community object
        #  to be passed instead of just the UUID as a string
        url = f'{self.API_ENDPOINT}/core/collections'
        params = None
        if parent is not None:
            params = {'parent': parent}
        return Collection(api_resource=parse_json(self.create_dso(url, params, data)))

    def get_item(self, uuid):
        """
        Get an item, given its UUID
        @param uuid:    the UUID of the item
        @return:        the raw API response
        """
        # TODO - return constructed Item object instead, handling errors here?
        url = f'{self.API_ENDPOINT}/core/items'
        try:
            id = UUID(uuid).version
            url = f'{url}/{uuid}'
            return self.api_get(url, None, None)
        except ValueError:
            print(f'Invalid item UUID: {uuid}')
            return None

    def create_item(self, parent, item):
        """
        Create an item beneath the given parent collection
        @param parent:  UUID of parent collection to pass as a parameter to create_dso
        @param item:    python Item object containing all the data and links expected by the REST API
        @return:        Item object constructed from the API response
        """
        url = f'{self.API_ENDPOINT}/core/items'
        if parent is None:
            print('Need a parent UUID!')
            return None
        params = {'owningCollection': parent}
        if not isinstance(item, Item):
            print('Need a valid item')
            return None
        return Item(api_resource=parse_json(self.create_dso(url, params=params, data=item.as_dict())))

    def update_item(self, item):
        """
        Update item. The Item passed to this method contains all the data, identifiers, links necessary to
        perform the update to the API. Note this is a full update, not a patch / partial update operation.
        @param item: python Item object
        @return:
        """
        if not isinstance(item, Item):
            print('Need a valid item')
            return None
        return self.update_dso(item, params=None)

    def add_metadata(self, dso, field, value, language=None, authority=None, confidence=-1, place=''):
        """
        Add metadata to a DSO using the api_patch method (PUT, with path and operation and value)
        :param dso:
        :param field:
        :param value:
        :param language:
        :param authority:
        :param confidence:
        :param place:
        :return:
        """
        if dso is None or field is None or value is None or not isinstance(dso, DSpaceObject):
            # TODO: separate these tests, and add better error handling
            print('Invalid or missing DSpace object, field or value string')
            return self

        dso_type = type(dso)

        # Place can be 0+ integer, or a hyphen - meaning "last"
        path = f'/metadata/{field}/{place}'
        patch_value = {
            'value': value,
            'language': language,
            'authority': authority,
            'confidence': confidence
        }

        url = dso.links['self']['href']

        r = self.api_patch(
            url=url, operation=self.PatchOperation.ADD, path=path, value=patch_value)

        return dso_type(api_resource=parse_json(r))

    def create_user(self, user, token=None):
        """
        Create a user
        @param user:    python User object or Python dict containing all the data and links expected by the REST API
        :param token:   Token if creating new user (optional) from the link in a registration email
        @return:        User object constructed from the API response
        """
        url = f'{self.API_ENDPOINT}/eperson/epersons'
        data = user
        if isinstance(user, User):
            data = user.as_dict()
            # TODO: Validation. Note, at least here I will just allow a dict instead of the pointless cast<->cast
            # that you see for other DSO types - still figuring out the best way
        params = None
        if token is not None:
            params = {'token': token}
        return User(api_resource=parse_json(self.create_dso(url, params=params, data=data)))

    def delete_user(self, user):
        if not isinstance(user, User):
            print(f'Must be a valid user')
            return None
        return self.delete_dso(user)

    def get_users(self):
        url = f'{self.API_ENDPOINT}/eperson/epersons'
        users = list()
        r = self.api_get(url)
        r_json = parse_json(response=r)
        if '_embedded' in r_json:
            if 'epersons' in r_json['_embedded']:
                for user_resource in r_json['_embedded']['epersons']:
                    users.append(User(user_resource))
        return users

    def create_group(self, group):
        """
        Create a group
        @param group:    python Group object or Python dict containing all the data and links expected by the REST API
        @return:         User object constructed from the API response
        """
        url = f'{self.API_ENDPOINT}/eperson/groups'
        data = group
        if isinstance(group, Group):
            data = group.as_dict()
            # TODO: Validation. Note, at least here I will just allow a dict instead of the pointless cast<->cast
            # that you see for other DSO types - still figuring out the best way
        return Group(api_resource=parse_json(self.create_dso(url, params=None, data=data)))
