import pandas as pd
import streamlit as st

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

# Load the Parquet file into a Pandas dataframe
@st.cache_data
def get_data():
    data = pd.read_parquet('Databases/System Record IDs')
    return data

data = get_data()

# Define the Streamlit app
st.title("Search for ID by Email address")

# Add a search box for email
search_box = st.text_input("Enter email address to search:")

# Filter the dataframe by the entered email and show the corresponding ID
if search_box:
    result = data.loc[data['address'].str.strip().str.match(search_box.strip(),case=False), 'constituent_id']

    if len(result.unique()) == 1:
        st.write("The ID for the entered email address is:")

        st.code(result.values[0])
        
    else:
        st.write("No ID found for the entered email. Kindly check manually in Raisers Edge.")