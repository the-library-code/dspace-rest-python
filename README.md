# DSpace Python REST Client Library
This client library allows Python 3 scripts (Python 2 probably compatible but not officially supported) to interact with
DSpace 7+ repositories, using the new REST API in DSpace that is used by its own user interface.

This library is a work in progress and so far offers basic create, update, retrieve functionality for
Community, Collection, Bundle, Item and Bitstream objects.

Help with extending the scope and improving the code is always welcome!

## Requirements
* Python 3.x (developed using Python 3.8.5)
* Python Requests module (see `requirements.txt`)
* Working DSpace 7 repository with an accessible REST API

## Usage
After installing dependencies, you're ready to run the script.
You can either pass the base API URL to the DSpaceClient() constructor or set them as environment variables.

## Example
See the `example.py` script for an example of community, collection, item, bundle and bitstream creation.
Just set the credentials and base URL at the top of the script to match your test system, or if you've set environment
variables, remove the arguments from the DSpaceClient() instantiation and the environment variables will be used as
defaults.

Install Requests, if not already installed: (use pyenv / virtualenv as you prefer!)
```commandline
╰─$ pip install requests                           
Collecting requests
  Downloading requests-2.27.1-py2.py3-none-any.whl (63 kB)
     |████████████████████████████████| 63 kB 980 kB/s 
Collecting urllib3<1.27,>=1.21.1
  Downloading urllib3-1.26.8-py2.py3-none-any.whl (138 kB)
     |████████████████████████████████| 138 kB 4.0 MB/s 
Collecting certifi>=2017.4.17
  Using cached certifi-2021.10.8-py2.py3-none-any.whl (149 kB)
Collecting charset-normalizer~=2.0.0; python_version >= "3"
  Downloading charset_normalizer-2.0.11-py3-none-any.whl (39 kB)
Collecting idna<4,>=2.5; python_version >= "3"
  Using cached idna-3.3-py3-none-any.whl (61 kB)
Installing collected packages: urllib3, certifi, charset-normalizer, idna, requests
Successfully installed certifi-2021.10.8 charset-normalizer-2.0.11 idna-3.3 requests-2.27.1 urllib3-1.26.8
```

Run the script:

```commandline
╰─$ python example.py                                                                                                                                                                                                              1 ↵
Updating token to 9730dfb9-c4ea-4f56-a2f0-4dc4cacf5059
Authenticated successfully as kim@shepherd.nz
API Post: Updating token to b44f91c2-5386-4c11-a1ca-1ea06613fae4
{"timestamp":"2022-02-10T05:44:12.758+00:00","status":403,"error":"Forbidden","message":"Access is denied. Invalid CSRF token.","path":"/server/api/core/communities"}
API Post: Retrying request with updated CSRF token
community 31264734-49c0-4bff-8ed7-e09e3abbfe7a created successfully!
New community created! Handle: 123456789/10
collection c010ef9c-2483-47c3-83af-8a8c1f72e888 created successfully!
New collection created! Handle: 123456789/11
item e59dfc7a-f96e-4897-a913-e962b220132b created successfully!
New item created! Handle: 123456789/12
New bundle created! UUID: 528d1dd9-ca62-4609-bb2e-1ab367299447
New bitstream created! UUID: 4740048b-25fa-4040-b0d1-4b27f13de75d
All finished with example data creation. Visit your test repository to review created objects
```

## Credits

Created by @kshepherd for The Library Code GmbH with support from Universität Hohenheim

## License

This work is licensed under the [BSD 3-Clause License](https://github.com/the-library-code/dspace-rest-python/blob/088169cdcb1a92ff33589b1af8c08a17f9885bbf/LICENSE)

Copyright 2021 The Library Code GmbH
