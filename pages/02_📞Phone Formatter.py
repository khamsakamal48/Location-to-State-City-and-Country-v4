import streamlit as st
import re
import pandas as pd

st.set_page_config(
    page_title='Phone Number Formatter',
    page_icon=':telephone_receiver:',
    layout="wide")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """            
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("Phone Number Formatter")

phone_number = st.text_input("Enter the phone number")

phone_number = re.sub("[^0-9]", "", phone_number)
st.write("<br>", unsafe_allow_html=True)

st.write("Formatted phone number:")

st.code(phone_number)

divider = '''
        <style>
        /* Rounded border */
        hr.rounded {
        border-top: 8px solid #bbb;
        border-radius: 5px;
        }
        </style>
        <hr class="rounded">
        '''

st.markdown(divider, unsafe_allow_html=True)

st.title("Country codes")

@st.cache_data
def get_data():
    data = pd.read_csv("Databases/Country Codes.csv")
    return data

data = get_data()

# Set table style
table_style = """
<style>
    table {
        width: 100%;
    }
    th {
        background-color: #4285f4;
        color: white;
        text-align: left;
    }
    th, td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }
    tr:hover {
        background-color: #f5f5f5;
    }
</style>
"""

# Render table
table_html = data.to_html(classes="data", header="true", index=False, justify='left')
table_html = table_html.replace('<table', '<table style="width:100%"')
table_html = f'<div style="overflow: auto;">{table_html}</div>'
st.write(table_html, unsafe_allow_html=True)
