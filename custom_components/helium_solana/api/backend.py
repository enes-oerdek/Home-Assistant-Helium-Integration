import time
import asyncio
import requests
from ..const import BACKEND_URL, BACKEND_KEY

class BackendAPI:
    def __init__(self, cache_ttl=600):
        self._cache = {}
        self._cache_ttl = cache_ttl

    @staticmethod
    def http_client(path, payload=None, method='GET', headers=None):
        # Make the HTTP request with the given URL, payload, method, and headers
        response = requests.request(method, BACKEND_URL+'/'+path, json=payload, headers=headers)

        # Raise an exception if the response was not successful
        response.raise_for_status()

        # Return the response
        return response

    async def get_data(self, path, cache_key=None):
        cache_key = cache_key or path  # Use the path as the cache key if no key is provided
        now = time.time()
        cache_entry = self._cache.get(cache_key)
        if cache_entry is None or now - cache_entry['time'] > self._cache_ttl:
            headers =  {'Authorization': 'bearer '+BACKEND_KEY }
            response = await asyncio.to_thread(self.http_client, path, None, 'GET', headers)
            self._cache[cache_key] = {'data': response, 'time': now}

        return self._cache[cache_key]['data']
