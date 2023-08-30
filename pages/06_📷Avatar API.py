import requests
import json
import streamlit as st

from urllib3 import Retry
from requests.adapters import HTTPAdapter

# API request strategy
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=['HEAD', 'GET', 'OPTIONS'],
    backoff_factor=10
)

adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount('https://', adapter)
http.mount('http://', adapter)

# Function to get pic
def get_pic(email, username, password):
    url = "https://avatarapi.com/v2/api.aspx"

    payload = {
        'username': username,
        'password': password,
        'email': email
    }

    headers = {
        'Content-Type': 'text/plain'
    }

    response = http.post(url, headers=headers, data=payload)

    if response.ok:
        return response['Image']
    else:
        return None

##### Webpage #######
st.title('Search Picture using email address')