import time
import asyncio
import requests
from ..const import BACKEND_URL, BACKEND_KEY

class BackendAPI:
    def __init__(self, cache_ttl=600):
        self._data = None
        self._cache_time = 0
        self._cache_ttl = cache_ttl

    @staticmethod
    def http_client(path, payload=None, method='GET', headers=None):
        # Make the HTTP request with the given URL, payload, method, and headers
        response = requests.request(method, BACKEND_URL+'/'+path, json=payload, headers=headers)

        # Raise an exception if the response was not successful
        response.raise_for_status()

        # Return the response
        return response

    async def get_data(self, path):
        now = time.time()
        if self._data is None or now - self._cache_time > self._cache_ttl:
            headers =  {'Authorization': 'bearer '+BACKEND_KEY }
            response = await asyncio.to_thread(self.http_client, path, None, 'GET', headers)
            self._data = response
            self._cache_time = now
        return self._data