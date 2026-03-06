# This software is licenced under the BSD 3-Clause licence
# available at https://opensource.org/licenses/BSD-3-Clause
# and described in the LICENSE.txt file in the root of this project

"""
DSpace REST API client library models.
Intended to make interacting with DSpace in Python 3 easier, particularly
when creating, updating, retrieving and deleting DSpace Objects.

@author Kim Shepherd <kim@shepherd.nz>
"""
import json

__all__ = ['DSpaceObject', 'HALResource', 'ExternalDataObject', 'SimpleDSpaceObject', 'Community',
           'Collection', 'Item', 'Bundle', 'Bitstream', 'BitstreamFormat', 'User', 'Group']


class HALResource:
    """
    Base class to represent HAL+JSON API resources
    """
    type = None

    def __init__(self, api_resource=None):
        """
        Default constructor
        @param api_resource: optional API resource (JSON) from a GET response or successful POST can populate instance
        """
        self.links = {}
        self.embedded = {} 

        if api_resource is not None:
            self.links = api_resource.get('_links', {}).copy()
            self.embedded = api_resource.get('_embedded', {}).copy()
        else:
            self.links = {'self': {'href': None}}

    def as_dict(self):
        return {'type': self.type}

class AddressableHALResource(HALResource):
    def __init__(self, api_resource=None):
        super().__init__(api_resource)
        self.id = None

        if api_resource is not None:
            self.id = api_resource.get('id')

    def as_dict(self):
        parent_dict = super().as_dict()
        this_dict = {'id': self.id}
        return {**parent_dict, **this_dict}

class ExternalDataObject(AddressableHALResource):
    """
    Generic External Data Object as configured in DSpace's external data providers framework
    TODO: this is also known as externalSourceEntry? Should the class name be modified or aliased?
    Or should we draw a subtle distinction between the two even if they share the same model
    """
    type = "externalSourceEntry"

    def __init__(self, api_resource=None):
        """
        Default constructor
        @param api_resource: optional API resource (JSON) from a GET response or successful POST can populate instance
        """
        super().__init__(api_resource)
        self.display = None
        self.value = None
        self.externalSource = None
        self.metadata = {}

        if api_resource is not None:
            self.display = api_resource.get('display')
            self.value = api_resource.get('value')
            self.externalSource = api_resource.get('externalSource')
            self.metadata = api_resource.get('metadata').copy()

    def get_metadata_values(self, field):
        """
        Return metadata values as simple list of strings
        @param field: DSpace field, eg. dc.creator
        @return: list of strings
        """
        return self.metadata.get(field, [])

    def as_dict(self):
        parent_dict = super().as_dict()
        edo_dict = {
            'display': self.display,
            'value': self.value,
            'externalSource': self.externalSource,
            'metadata': self.metadata,
        }
        return {**parent_dict, **edo_dict}

class DSpaceObject(AddressableHALResource):
    """
    Base class to represent DSpaceObject API resources
    The variables here are present in an _embedded response and the ones required for POST / PUT / PATCH
    operations are included in the dict returned by asDict(). Implements toJSON() as well.
    This class can be used on its own but is generally expected to be extended by other types: Item, Bitstream, etc.
    """

    def __init__(self, api_resource=None, dso=None):
        """
        Default constructor
        @param api_resource: optional API resource (JSON) from a GET response or successful POST can populate instance
        """
        super().__init__(api_resource)
        self.uuid = None
        self.name = None
        self.handle = None
        self.lastModified = None
        self.parent = None
        self.metadata = {}

        if dso is not None:
            api_resource = dso.as_dict()
            self.links = dso.links.copy()

        if api_resource is not None:
            self.id = api_resource.get('id')
            self.uuid = api_resource.get('uuid')
            self.name = api_resource.get('name')
            self.handle = api_resource.get('handle')
            self.metadata = api_resource.get('metadata', {}).copy()
            self.lastModified = api_resource.get('lastModified')
            # Python interprets _ prefix as private so for now, renaming this and handling it separately
            # alternatively - each item could implement getters, or a public method to return links
            self.links = api_resource.get('_links', {}).copy()

    def add_metadata(self, field, value, language=None, authority=None, confidence=-1, place=None):
        """
        Add metadata to a DSO. This is performed on the local object only, it is not an API operation (see patch)
        This is useful when constructing new objects for ingest.
        When doing simple changes like "retrieve a DSO, add some metadata, update" then it is best to use a patch
        operation, not this clas method. See
        :param field:
        :param value:
        :param language:
        :param authority:
        :param confidence:
        :param place:
        :return:
        """
        if field is None or value is None:
            return
        values = self.metadata.get(field, [])
        # Ensure we don't accidentally duplicate place value. If this place already exists, the user
        # should use a patch operation or we should allow another way to re-order / re-calc place?
        # For now, we'll just set place to none if it matches an existing place
        for v in values:
            if v['place'] == place:
                place = None
                break
        values.append({"value": value, "language": language,
                       "authority": authority, "confidence": confidence, "place": place})
        self.metadata[field] = values

        # Return this as an easy way for caller to inspect or use
        return self

    def clear_metadata(self, field=None, value=None):
        if field is None:
            self.metadata = {}
        elif field in self.metadata:
            if value is None:
                self.metadata.pop(field)
            else:
                updated = []
                for v in self.metadata[field]:
                    if v != value:
                        updated.append(v)
                self.metadata[field] = updated

    def as_dict(self):
        """
        Return custom dict of this DSpaceObject with specific attributes included (no _links, etc.)
        @return: dict of this DSpaceObject for API use
        """
        parent_dict = super().as_dict()
        dso_dict = {
            'uuid': self.uuid,
            'name': self.name,
            'handle': self.handle,
            'metadata': self.metadata,
            'lastModified': self.lastModified
        }
        return {**parent_dict, **dso_dict}

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=None)

    def to_json_pretty(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class SimpleDSpaceObject(DSpaceObject):
    """
    Objects that share similar simple API methods eg. PUT update for full metadata replacement, can have handles, etc.
    By default this is Item, Community, Collection classes
    """


class Item(SimpleDSpaceObject):
    """
    Extends DSpaceObject to implement specific attributes and functions for items
    """
    type = "item"

    def __init__(self, api_resource=None, dso=None):
        """
        Default constructor. Call DSpaceObject init then set item-specific attributes
        @param api_resource: API result object to use as initial data
        """
        self.inArchive = False
        self.discoverable = False
        self.withdrawn = False
        self.metadata = {}
        if dso is not None:
            api_resource = dso.as_dict()
            super().__init__(dso=dso)
        else:
            super().__init__(api_resource)

        if api_resource is not None:
            self.inArchive = api_resource.get('inArchive', True)
            self.discoverable = api_resource.get('discoverable', False)
            self.withdrawn = api_resource.get('withdrawn', False)

    def get_metadata_values(self, field):
        """
        Return metadata values as simple list of strings
        @param field: DSpace field, eg. dc.creator
        @return: list of strings
        """
        return self.metadata.get(field, [])

    def as_dict(self):
        """
        Return a dict representation of this Item, based on super with item-specific attributes added
        @return: dict of Item for API use
        """
        dso_dict = super().as_dict()
        item_dict = {'inArchive': self.inArchive, 'discoverable': self.discoverable, 'withdrawn': self.withdrawn}
        return {**dso_dict, **item_dict}

    @classmethod
    def from_dso(cls, dso: DSpaceObject):
        # Create new Item and copy everything over from this dso
        item = cls()
        for key, value in dso.__dict__.items():
            item.__dict__[key] = value
        return item


class Community(SimpleDSpaceObject):
    """
    Extends DSpaceObject to implement specific attributes and functions for communities
    """
    type = 'community'

    def __init__(self, api_resource=None):
        """
        Default constructor. Call DSpaceObject init then set item-specific attributes
        @param api_resource: API result object to use as initial data
        """
        super().__init__(api_resource)

    def as_dict(self):
        """
        Return a dict representation of this Community, based on super with community-specific attributes added
        @return: dict of Item for API use
        """
        dso_dict = super().as_dict()
        # TODO: More community-specific stuff
        community_dict = {}
        return {**dso_dict, **community_dict}


class Collection(SimpleDSpaceObject):
    """
    Extends DSpaceObject to implement specific attributes and functions for collections
    """
    type = "collection"

    def __init__(self, api_resource=None):
        """
        Default constructor. Call DSpaceObject init then set collection-specific attributes
        @param api_resource: API result object to use as initial data
        """
        super().__init__(api_resource)

    def as_dict(self):
        dso_dict = super().as_dict()
        """
        Return a dict representation of this Collection, based on super with collection-specific attributes added
        @return: dict of Item for API use
        """
        collection_dict = {}
        return {**dso_dict, **collection_dict}


class Bundle(DSpaceObject):
    """
    Extends DSpaceObject to implement specific attributes and functions for bundles
    """
    type = "collection"

    def __init__(self, api_resource=None):
        """
        Default constructor. Call DSpaceObject init then set bundle-specific attributes
        @param api_resource: API result object to use as initial data
        """
        super().__init__(api_resource)

    def as_dict(self):
        """
        Return a dict representation of this Bundle, based on super with bundle-specific attributes added
        @return: dict of Bundle for API use
        """
        dso_dict = super().as_dict()
        bundle_dict = {}
        return {**dso_dict, **bundle_dict}


class Bitstream(DSpaceObject):
    """
    Extends DSpaceObject to implement specific attributes and functions for bundles
    """
    type = "bitstream"

    def __init__(self, api_resource=None):
        """
        Default constructor. Call DSpaceObject init then set bitstream-specific attributes
        @param api_resource: API result object to use as initial data
        """
        super().__init__(api_resource)
        # Bitstream has a few extra fields specific to file storage
        self.bundleName = None
        self.sizeBytes = None
        self.checkSum = {
            'checkSumAlgorithm': 'MD5',
            'value': None
        }
        self.sequenceId = None

        if api_resource is not None:
            self.bundleName = api_resource.get('bundleName')
            self.sizeBytes = api_resource.get('sizeBytes')
            self.checkSum = api_resource.get('checkSum', self.checkSum)
            self.sequenceId = api_resource.get('sequenceId')

    def as_dict(self):
        """
        Return a dict representation of this Bitstream, based on super with bitstream-specific attributes added
        @return: dict of Bitstream for API use
        """
        dso_dict = super().as_dict()
        bitstream_dict = {'bundleName': self.bundleName, 'sizeBytes': self.sizeBytes, 'checkSum': self.checkSum,
                          'sequenceId': self.sequenceId}
        return {**dso_dict, **bitstream_dict}

class BitstreamFormat(AddressableHALResource):
    """
    Bitstream format: https://github.com/DSpace/RestContract/blob/main/bitstreamformats.md
    example:
        {
          "shortDescription": "XML",
          "description": "Extensible Markup Language",
          "mimetype": "text/xml",
          "supportLevel": "KNOWN",
          "internal": false,
          "extensions": [
                  "xml"
          ],
          "type": "bitstreamformat"
        }
    """
    type = "bitstreamformat"

    def __init__(self, api_resource):
        super(BitstreamFormat, self).__init__(api_resource)
        self.shortDescription = None
        self.description = None
        self.mimetype = None
        self.supportLevel = None
        self.internal = False
        self.extensions = []

        if api_resource is not None:
            self.shortDescription = api_resource.get('shortDescription')
            self.description = api_resource.get('description')
            self.mimetype = api_resource.get('mimetype')
            self.supportLevel = api_resource.get('supportLevel')
            self.internal = api_resource.get('internal')
            self.extensions = api_resource.get('extensions', {}).copy()

    def as_dict(self):
        parent_dict = super(BitstreamFormat, self).as_dict()
        dict = {
            'shortDescription': self.shortDescription,
            'description': self.description,
            'mimetype': self.mimetype,
            'supportLevel': self.supportLevel,
            'internal': self.internal,
            'extensions': self.extensions
        }
        return {**parent_dict, **dict}

class Group(DSpaceObject):
    """
    Extends DSpaceObject to implement specific attributes and methods for groups (aka. EPersonGroups)
    """
    type = 'group'

    def __init__(self, api_resource=None):
        """
        Default constructor. Call DSpaceObject init then set group-specific attributes
        @param api_resource: API result object to use as initial data
        """
        super().__init__(api_resource)
        self.name = None
        self.permanent = False

        if api_resource is not None:
            self.name = api_resource.get('name')
            self.permanent = api_resource.get('permanent')

    def as_dict(self):
        """
        Return a dict representation of this Group, based on super with group-specific attributes added
        @return: dict of Group for API use
        """
        dso_dict = super().as_dict()
        group_dict = {'name': self.name, 'permanent': self.permanent}
        return {**dso_dict, **group_dict}


class User(SimpleDSpaceObject):
    """
    Extends DSpaceObject to implement specific attributes and methods for users (aka. EPersons)
    """
    type = "eperson"

    def __init__(self, api_resource=None):
        """
        Default constructor. Call DSpaceObject init then set user-specific attributes
        @param api_resource: API result object to use as initial data
        """
        super().__init__(api_resource)
        self.name = None
        self.netid = None
        self.lastActive = None
        self.canLogIn = False
        self.email = None
        self.requireCertificate = False
        self.selfRegistered = False

        if api_resource is not None:
            self.name = api_resource.get('name')
            self.netid = api_resource.get('netid')
            self.lastActive = api_resource.get('lastActive')
            self.canLogIn = api_resource.get('canLogIn')
            self.email = api_resource.get('email')
            self.requireCertificate = api_resource.get('requireCertificate')
            self.selfRegistered = api_resource.get('selfRegistered')

    def as_dict(self):
        """
        Return a dict representation of this User, based on super with user-specific attributes added
        @return: dict of User for API use
        """
        dso_dict = super().as_dict()
        user_dict = {'name': self.name, 'netid': self.netid, 'lastActive': self.lastActive, 'canLogIn': self.canLogIn,
                     'email': self.email, 'requireCertificate': self.requireCertificate,
                     'selfRegistered': self.selfRegistered}
        return {**dso_dict, **user_dict}

class InProgressSubmission(AddressableHALResource):

    def __init__(self, api_resource):
        super().__init__(api_resource)
        self.lastModified = None
        self.step = None
        self.sections = {}

        if api_resource is not None:
            self.lastModified = api_resource.get('lastModified')
            self.step = api_resource.get('lastModified')
            self.sections = api_resource.get('sections', {}).copy()
            self.lastModified = api_resource.get('lastModified')

    def as_dict(self):
        parent_dict = super().as_dict()
        dict = {
            'lastModified': self.lastModified,
            'step': self.step,
            'sections': self.sections,
        }
        return {**parent_dict, **dict}

class WorkspaceItem(InProgressSubmission):
    type = 'workspaceitem'

    def __init__(self, api_resource):
        super().__init__(api_resource)

    def as_dict(self):
        return super().as_dict()

class EntityType(AddressableHALResource):
    """
    Extends Addressable HAL Resource to model an entity type (aka item type)
    used in entities and relationships. For example, Publication, Person, Project and Journal
    are all common entity types used in DSpace 7+
    """
    type = "entitytype"

    def __init__(self, api_resource):
        super().__init__(api_resource)
        self.label = None

        if api_resource is not None:
            self.label = api_resource.get('label')

class RelationshipType(AddressableHALResource):
    """
    TODO: RelationshipType
    """
    type = "relationshiptype"

    def __init__(self, api_resource):
        super().__init__(api_resource)

class SearchResult(HALResource):
    """
    Discover search result 
    """
    type = "discover"

    def __init__(self, api_resource):
        super().__init__(api_resource)
        self.query = None
        self.scope = None
        self.appliedFilters = [] 

        if api_resource is not None:
            self.lastModified = api_resource.get('lastModified')
            self.step = api_resource.get('step')
            self.sections = api_resource.get('sections', {}).copy()

    def as_dict(self):
        parent_dict = super().__dict__
        dict = {
            'lastModified': self.lastModified,
            'step': self.step,
            'sections': self.sections,
        }
        return {**parent_dict, **dict}

class ResourcePolicy(AddressableHALResource):
    """
    A resource policy to control access and authorization to DSpace objects
    See: https://github.com/DSpace/RestContract/blob/main/resourcepolicies.md
    """
    type = "resourcepolicy"

    def __init__(self, api_resource):
        super().__init__(api_resource)
        self.name = None
        self.description = None
        self.policyType = None
        self.action = None
        self.startDate = None
        self.endDate = None

        if api_resource is not None:
            self.name = api_resource.get('name')
            self.description = api_resource.get('description')
            self.policyType = api_resource.get('policyType')
            self.action = api_resource.get('action')
            self.startDate = api_resource.get('startDate')
            self.endDate = api_resource.get('endDate')

    def as_dict(self):
        hal_dict = super().as_dict()
        rp_dict = {'name': self.name, 'description': self.description, 'policyType': self.policyType,
                   'action': self.action, 'startDate': self.startDate, 'endDate': self.endDate}
        return {**hal_dict, **rp_dict}


