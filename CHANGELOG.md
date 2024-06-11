# Changelog

### 0.1.11

Date: 2024-06-11

PyPI release page: https://pypi.org/project/dspace-rest-client/0.1.11/

**Changes**

1. Small changes to maintenance docs and publish script
2. Correct required packages in `requirements.txt` and `setup.py` as per https://github.com/the-library-code/dspace-rest-python/issues/16 (reported by @alanorth)

### 0.1.10

Date: 2024-04-04

PyPI release page: https://pypi.org/project/dspace-rest-client/0.1.10/

**Changes**

1. Correct content type header for URI tests: https://github.com/the-library-code/dspace-rest-python/pull/14 (thanks to @andreasgeissner)
2. Small change to example script checks for successful bitstream header retrieve before printing
3. Added new `MAINTAINING.md` to keep notes about build and publish process with the rest of the project files

### 0.1.9

Date: 2023-12-03

PyPI release page: https://pypi.org/project/dspace-rest-client/0.1.9/

**Changes**

1. All `print` statements in client module replaced with Python logging: https://github.com/the-library-code/dspace-rest-python/issues/12
2. A customisable user agent header is added to each request, to allow for better logging at the
API endpoint and to force requests through Cloudfront, other WAF proxies that filter
requests by user agent. Reported by @abubelinha: https://github.com/the-library-code/dspace-rest-python/issues/10
3. In the `search_objects` client method, the `dsoType` arg is renamed to `dso_type` to conform with
PEP 8 style guidlelines, and a new `scope` arg is added to restrict the search to a particular collection or community.
4. A new `get_items` client method is added, to get all items (admin-only)
5. A new `get_short_lived_token` client method is added, for bitstream retrieval
6. A new `download_bitstream` client method is added to retrieve actual /content
7. A new `example_gets.py` script is added, and `example.py` updated to include basic examples of how to retrieve, iterate and work with existing data in the repository. Reported by @pnbecker: https://github.com/the-library-code/dspace-rest-python/issues/11
8. pysolr added to requirements.txt to satisfy this solr client dependency missing from the last version: https://github.com/the-library-code/dspace-rest-python/issues/7

### 0.1.8

PyPI release page: https://pypi.org/project/dspace-rest-client/0.1.8/

Date: 2023-10-07

**Changes**

Fixes a bug when using get_communities with a uuid parameter to fetch a single community, 
see: https://github.com/the-library-code/dspace-rest-python/issues/8