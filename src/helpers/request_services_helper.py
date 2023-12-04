import requests
import urllib3
from random import uniform

urllib3.disable_warnings()


def get_url(url: str):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) '
                      'Gecko/20100101 Firefox/52.0'
    }
    timeout = uniform(0.5, 0.9)

    return requests.get(url=url, headers=headers, verify=False)
