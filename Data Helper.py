#Import the required Libraries
import streamlit as st

st.set_page_config(layout="wide")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """            
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Add a title and intro text
st.title('Data Helper')
st.text('This is a web app to assist in Data Cleaning and Processinsg.')