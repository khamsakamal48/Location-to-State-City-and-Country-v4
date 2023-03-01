import pandas as pd
import streamlit as st
import pyperclip

st.set_page_config(
    page_title='Search Raisers Edge ID against contact information',
    page_icon=':mag:',
    layout="wide")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """            
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Load the CSV file into a Pandas dataframe
@st.cache_data
def get_data():
    data = pd.read_csv('Databases/System Record IDs.CSV', encoding='latin1')
    return data

data = get_data()

def copy_to_clipboard(text):
    pyperclip.copy(text)
    st.success("Copied to clipboard!")

# Define the Streamlit app
st.title("Search for ID by contact details")

# Add a search box for email
search_box = st.text_input("Enter contact detail to search:")

# Filter the dataframe by the entered email and show the corresponding ID
if search_box:
    result = data.loc[data['Phone Number'] == search_box, 'System Record ID'].values
    if result:
        st.write("The ID for the entered contact is:")
        # result = str(result[0])

        st.code(result[0])
        
    else:
        st.write("No ID found for the entered contact.")