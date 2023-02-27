import requests
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.environ.get('API_KEY')

st.title('Find City, State and Country')

address = st.text_input('Enter address or location')
if st.button('Geocode'):
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}'
    response = requests.get(url).json()
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
        st.write(f'City: {city}')
        st.write(f'State: {state}')
        st.write(f'Country: {country}')
    else:
        st.error('Unable to geocode address')
