# utility.py
import requests
from requests.exceptions import RequestException

def http_client(url, payload=None, method='GET', headers=None):
    try:
        # Make the HTTP request with the given URL, payload, method, and headers
        response = requests.request(method, url, json=payload, headers=headers)

        # Raise an exception if the response was not successful
        response.raise_for_status()

    except RequestException as e:
        print(f"An error occurred while making a request to {url}: {str(e)}")
        return None

    # Return the response
    return response

def title_case_and_replace_hyphens(input_string: str) -> str:
    return input_string.replace("-", " ").title()