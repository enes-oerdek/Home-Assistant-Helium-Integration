import time
import asyncio
import requests

class HeliumStatsAPI:
    def __init__(self, url, token, cache_ttl=300):
        self.url = url
        self._data = None
        self._cache_time = 0
        self._cache_ttl = cache_ttl
        self.token = token;
        
    @staticmethod
    def http_client(url, payload=None, method='GET', headers=None):
        # Make the HTTP request with the given URL, payload, method, and headers
        response = requests.request(method, url, json=payload, headers=headers)

        # Raise an exception if the response was not successful
        response.raise_for_status()

        # Return the response
        return response

    async def get_data(self):
        now = time.time()
        if self._data is None or now - self._cache_time > self._cache_ttl:
            headers =  {'Authorization': 'bearer '+self.token }
            response = await asyncio.to_thread(self.http_client, self.url, None, 'GET', headers)
            self._data = response
            self._cache_time = now
        return self._data