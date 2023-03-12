import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title='Database KPI Tracker',
    page_icon=':dart:',
    layout="wide",
    initial_sidebar_state='expanded')

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
    data = pd.read_parquet('Databases/Custom Fields')
    return data

data = get_data()

# ---- SIDEBAR ----
st.sidebar.header('Filters')
## Create a sidebar filter for date range
start_date = st.sidebar.date_input("Start date", value=data['date_added'].min())
end_date = st.sidebar.date_input("End date", value=data['date_added'].max())

# Convert start_date and end_date to datetime64[ns, UTC] objects
start_date = pd.Timestamp(start_date, tz='UTC')
end_date = pd.Timestamp(end_date, tz='UTC')

## Create a sidebar filter for verified_source
verified_source = st.sidebar.multiselect(
    "Select the sources for verified contact details:",
    options=data[data['category'].str.contains('Verified', case=False)]['verified_source'].unique(),
    # default=data[(data['category'].str.contains('Verified', case=False)) & (data['comment'] != 'verified using RE appeal data')]['verified_source'].unique()
    default=data[data['category'].str.contains('Verified', case=False)]['verified_source'].unique()
)

verified_contacts = data.query(
    "verified_source == @verified_source and @start_date <= date_added <= @end_date"
)

# Verified Emails
# Getting the count for metrics
verified_emails = verified_contacts[verified_contacts['category'] == 'Verified Email']['parent_id'].nunique()

## Formatting it as proper readable numbers
verified_emails = "{:,}".format(verified_emails)

# Verified Phones
# Getting the count for metrics
verified_phone = verified_contacts[verified_contacts['category'] == 'Verified Phone']['parent_id'].nunique()

## Formatting it as proper readable numbers
verified_phone = "{:,}".format(verified_phone)

## Create a sidebar filter for verified_source
sync_source = st.sidebar.multiselect(
    "Select the sources for updates:",
    options=data[data['sync_source'].notnull()]['sync_source'].unique(),
    # default=data[(data['category'].str.contains('Verified', case=False)) & (data['comment'] != 'verified using RE appeal data')]['verified_source'].unique()
    default=data[data['sync_source'].notnull()]['sync_source'].unique()
)

# Updates
updates = data.query(
    "sync_source == @sync_source and @start_date <= date_added <= @end_date and sync_source.notnull()"
)

## Email Updates
email_updates = updates[updates['update_type'] == 'Email']['parent_id'].nunique()
email_updates = "{:,}".format(email_updates)

## Phone Updates
phone_updates = updates[updates['update_type'] == 'Phone']['parent_id'].nunique()
phone_updates = "{:,}".format(phone_updates)

## Location Updates
location_updates = updates[updates['update_type'] == 'Location']['parent_id'].nunique()
location_updates = "{:,}".format(location_updates)

## Employment Updates
employment_updates = updates[updates['update_type'] == 'Employment']['parent_id'].nunique()
employment_updates = "{:,}".format(employment_updates)

## Online Presence Updates
online_presence_updates = updates[updates['update_type'] == 'Online Presence']['parent_id'].nunique()
online_presence_updates = "{:,}".format(online_presence_updates)

## Education Updates
education_updates = updates[updates['update_type'] == 'Education']['parent_id'].nunique()
education_updates = "{:,}".format(education_updates)

## Bio Updates
bio_updates = updates[updates['update_type'] == 'Bio Details']['parent_id'].nunique()
bio_updates = "{:,}".format(bio_updates)

## New Alum Updates
new_alums = updates[updates['update_type'] == 'New Alums']['parent_id'].nunique()
new_alums = "{:,}".format(new_alums)

# ---- MAINPAGE ----
st.title(":dart: Database KPI Tracker")
st.markdown("##")

# Row A
st.markdown('## Verified Contacts')
col1, col2 = st.columns(2)
col1.metric("Email", verified_emails)
col2.metric("Phone", verified_phone)

# Row B
# Combine verified_emails and verified_phone into a single dataframe
# Verified Emails
# Getting the count for metrics
verified_emails = verified_contacts[verified_contacts['category'] == 'Verified Email']
verified_emails = verified_emails.resample('M', on='date_added').count().reset_index()
verified_emails['date_added'] = verified_emails['date_added'].dt.strftime('%b\'%y')
verified_emails.rename(columns={'parent_id': 'Emails'}, inplace=True)

# Verified Phones
# Getting the count for metrics
verified_phone = verified_contacts[verified_contacts['category'] == 'Verified Phone']
verified_phone = verified_phone.resample('M', on='date_added').count().reset_index()
verified_phone['date_added'] = verified_phone['date_added'].dt.strftime('%b\'%y')
verified_phone.rename(columns={'parent_id': 'Phones'}, inplace=True)

merged_df = pd.merge(verified_emails, verified_phone, on='date_added', how='outer')

st.markdown('###')
st.markdown('##### Monthly Trend')
fig = px.line(merged_df, x='date_added', y=['Emails', 'Phones'], width=None, line_shape='spline')
fig.update_traces(mode='lines+markers', line_width=4, marker_size=11)
fig.update_layout(
    xaxis_tickformat='%b\'%y',
    xaxis_title='',
    yaxis_title='Verified Contacts',
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        title=dict(text='')
    ),
    margin=dict(l=0, r=0, t=0, b=0)
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("""---""")

# Row C
st.markdown('## Database Update Summary')
col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
col1.metric("Email", email_updates)
col2.metric("Phone", phone_updates)
col3.metric("Location", location_updates)
col4.metric("Employment", employment_updates)
col5.metric("Online Presence", online_presence_updates)
col6.metric("Education", education_updates)
col7.metric("Bio Details", bio_updates)
col8.metric("New Alums", new_alums)

st.markdown('###')
st.markdown('##### Monthly Trend')
line_chart_data = updates.groupby([pd.Grouper(key='date_added', freq='M'), 'update_type']).size().reset_index(name='count')
line_chart_data['date_added'] = line_chart_data['date_added'].dt.strftime('%b\'%y')
# line_chart_data = line_chart_data.groupby([pd.Grouper(key='date_added', freq='M'), 'update_type']).sum().reset_index()
# line_chart_data = line_chart_data.sort_values(by='date_added')

# # Extract the month and year from the date_column
# line_chart_data['month'] = pd.DatetimeIndex(line_chart_data['date_added']).month
# line_chart_data['year'] = pd.DatetimeIndex(line_chart_data['date_added']).year

# # Sort the DataFrame by month and year
# line_chart_data = line_chart_data.sort_values(by=['year', 'month'])

# line_chart_data['date_added'] = line_chart_data['date_added'].dt.strftime('%b\'%y')

line_chart = px.line(line_chart_data, x='date_added', y='count', color='update_type', width=None, line_shape='spline')
line_chart.update_traces(mode='lines+markers', line_width=4, marker_size=11)
line_chart.update_layout(
    xaxis_tickformat='%b\'%y',
    xaxis_title='',
    yaxis_title='Updates',
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        title=dict(text='')
    ),
    margin=dict(l=0, r=0, t=0, b=0)
)
st.plotly_chart(line_chart, use_container_width=True)
