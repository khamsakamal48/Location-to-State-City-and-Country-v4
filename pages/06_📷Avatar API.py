import requests
import re
import streamlit as st

from urllib3 import Retry
from requests.adapters import HTTPAdapter

st.set_page_config(
    page_title='Search Picture using email address',
    page_icon=':camera:',
    layout="wide",
    initial_sidebar_state='expanded')

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

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
        'Content-Type': 'application/json'
    }

    response = http.post(url, headers=headers, params=payload, json=payload).json()

    return response

def is_valid_email(email: str) -> bool:
    """
    This function checks if the given email address is valid.
    :param email: str, the email address to be checked
    :return: bool, True if the email address is valid, False otherwise
    """
    # Define a regular expression pattern for a valid email address
    pattern = r'^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$'

    # Use the re module to check if the email address matches the pattern
    return bool(re.match(pattern, email))

##### Webpage #######
st.title('Search Picture using email address')

st.sidebar.header('Enter your AvatarAPI credentials')
st.sidebar.write('Username')
username = st.sidebar.text_input('Username', label_visibility='collapsed')
st.sidebar.write('Password')
password = st.sidebar.text_input('Password', type='password', label_visibility='collapsed')

st.markdown('#')
st.header('Enter the email address')
email = st.text_input('Email address', placeholder='Enter the email address for which you want to search the Profile picture', label_visibility='collapsed')
email = email.strip()

if st.button('Check for Picture', use_container_width=True):
    if username and password:
        if email:
            if is_valid_email(email):
                response = get_pic(email, username, password)

                st.divider()

                if response:
                    try:
                        pic = response['Image']
                        col1, col2, col3 = st.columns(3)
                        col2.image(pic, use_column_width='auto')

                    except:
                        if response['Error'] == 'Not found':
                            st.warning('No image found', icon='😔')

                        else:
                            st.error('An error occurred', icon='⚠️')
                            st.json(response)

                else:
                    st.error('An error occurred', icon='⚠️')
                    st.json(response)

            else:
                st.error('Please enter a valid email address', icon='⚠️')
        else:
            st.warning('Please enter an email address...', icon='🙏')
    else:
        st.warning('Please enter your AvatarAPI credentials...', icon='🙏')

st.sidebar.divider()
st.sidebar.write("""
Kindly create account by visiting https://avatarapi.com to get the credentials.
""")