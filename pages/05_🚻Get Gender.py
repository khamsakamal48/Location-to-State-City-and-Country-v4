import streamlit as st
import pandas as pd
import numpy as np
import pickle
from tensorflow import keras
from sklearn.metrics import f1_score
import unicodedata

st.set_page_config(
    page_title='Gender Identifier',
    page_icon=':transgender_symbol:',
    layout="wide")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Add title and description to app
st.title(':transgender_symbol: Gender Identifier')
st.markdown("##")
st.write('##### Enter First name to predict the gender of the person.')

#word encoding
maxlen = 20                                               # max length of a name
# vocab = set(' '.join([str(i) for i in names]))            # creating a vocab
# vocab.add('END')
vocab = {' ',
         'END',
         'a',
         'b',
         'c',
         'd',
         'e',
         'f',
         'g',
         'h',
         'i',
         'j',
         'k',
         'l',
         'm',
         'n',
         'o',
         'p',
         'q',
         'r',
         's',
         't',
         'u',
         'v',
         'w',
         'x',
         'y',
         'z'}
len_vocab = len(vocab)
char_index = dict((c, i) for i, c in enumerate(vocab))    # creating a dictionary

# Builds an empty line with a 1 at the index of character
def set_flag(i):
    aux = np.zeros(len_vocab);
    aux[i] = 1
    return list(aux)

# Truncate names and create the matrix
def prepare_encod_names(X):
    vec_names = []
    trunc_name = [str(i)[0:maxlen] for i in X]  # consider only the first 20 characters
    for i in trunc_name:
        tmp = [set_flag(char_index.get(j, char_index[" "])) for j in str(i)]
        for k in range(0, maxlen - len(str(i))):
            tmp.append(set_flag(char_index["END"]))
        vec_names.append(tmp)
    return vec_names

@st.cache_resource(show_spinner='Loading the Machine Learning Model...')
def load_model():
    # Load the trained model
    model_path = 'Models/model.h5'
    custom_objects = {'f1_score': f1_score}
    loaded_model = keras.models.load_model(model_path, custom_objects=custom_objects)
    return loaded_model

loaded_model = load_model()

@st.cache_data
# Load the tokenizer
def load_token():
    tokenizer_path = 'Models/tokenizer.pickle'
    with open(tokenizer_path, 'rb') as file:
        return pickle.load(file)

tokenizer = load_token()

# Load the char_index dictionary
def load_index():
    char_index_path = 'Models/char_index.pickle'
    with open(char_index_path, 'rb') as file:
        return pickle.load(file)

char_index = load_index()

name = st.text_input("First Name")

# Else
st.markdown("##")
st.write('##### Else, upload first names as per the template to do bulk predictions.')
# Add file uploader for CSV file
uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
st.markdown("##")

def predict_gender(name):
    try:
        name = name.lower()
    except:
        name = name.casefold()

    # Normalize the name to remove diacritic marks and special characters
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')

    name = prepare_encod_names([name])  # Now the names are encod as a vector of numbers with weight
    resu = (loaded_model.predict(name) > 0.5).astype("int32")
    if int(resu) == 1:
        return ('Male')
    else:
        return ('Female')

if st.button("Predict"):
    if name:
        gender = predict_gender(name)
        st.write(f"The name '{name}' is most likely associated with {gender}.")
    elif uploaded_file:
        # Load CSV file into a pandas dataframe
        df = pd.read_csv(uploaded_file)
        # Predict the gender for each name in the dataframe
        df['gender'] = df['name'].apply(predict_gender)
        # Download the dataframe as a CSV file with predicted gender
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download the processed file",
            data=csv,
            file_name="gender_predictions.csv",
            mime="text/csv"
        )
    else:
        st.write("Please enter a name or upload a CSV file to predict the gender.")

st.markdown("""---""")
st.markdown("##")
st.markdown('#### Data Upload Format')
st.markdown("##")
st.write('##### Download below template to predict gender of multiple names at once.')
st.write("Don't forget to upload the CSV file after filling.")

with open('Templates/name_upload_template.csv') as f:
    st.download_button(
        label="Download Template",
        data=f,
        file_name="name_upload_template.csv",
        mime="text/csv"
    )