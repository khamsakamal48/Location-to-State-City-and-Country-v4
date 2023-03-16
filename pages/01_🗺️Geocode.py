import requests
import streamlit as st
from dotenv import load_dotenv
import os

st.set_page_config(
    page_title='Address Geocoder',
    page_icon=':round_pushpin:',
    layout="wide")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """            
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

load_dotenv()
api_key = os.getenv('API_KEY')

# Set Proxy
http_proxy = os.environ.get('HTTP_PROXY')
https_proxy = os.environ.get('HTTPS_PROXY')
proxies = {}
if http_proxy:
    proxies['http'] = http_proxy
if https_proxy:
    proxies['https'] = https_proxy

st.title('Find City, State and Country')

address = st.text_input('Enter address or location')
if st.button('Geocode'):
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}&language=en'
    response = requests.get(url, proxies=proxies, verify=False).json()
    if response['status'] == 'OK':
        results = response['results'][0]
        city = state = country = ''
        for component in results['address_components']:
            if 'locality' in component['types']:
                city = component['long_name']
            elif 'administrative_area_level_1' in component['types']:
                state = component['long_name']
            elif 'country' in component['types']:
                country = component['long_name']
                
        st.write('City:')
        st.code(city)
        
        st.write('State:')
        st.code(state)
        
        st.write('Country:')
        st.code(country)
    
    else:
        st.error('Unable to geocode address')