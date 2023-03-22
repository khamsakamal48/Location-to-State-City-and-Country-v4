import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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

# Plotly Configuration
plotly_config = {
    'displaylogo': False,
    'toImageButtonOptions': {
        'format': 'png', # one of png, svg, jpeg, webp
        'filename': 'custom_image',
        'height': 1080,
        'width': 1920,
        'scale': 2 # Multiply title/legend/axis/canvas sizes by this factor
    }
}

# Load the Parquet file into a Pandas dataframe
@st.cache_data(ttl=43200) # Reset cache after 12 Hours
def get_data():
    data = pd.read_parquet('Databases/Custom Fields')
    # Reset the index so that the date column becomes a regular column
    data = data.reset_index(drop=True)
    return data

data = get_data()

# ---- SIDEBAR ----
st.sidebar.header('Filters')
## Create a sidebar filter for date range
start_date = st.sidebar.date_input("Start date", value=data['date'].min())
end_date = st.sidebar.date_input("End date", value=data['date'].max())

start_date = pd.Timestamp(start_date)
end_date = pd.Timestamp(end_date)

## Create a sidebar filter for verified_source
shortlisted_data = data.query(
    "@start_date <= date <= @end_date"
).reset_index(drop=True)

verified_source = st.sidebar.multiselect(
    "Select the sources for verified contact details:",
    options=shortlisted_data[shortlisted_data['category'].str.contains('Verified', case=False)]['verified_source'].sort_values().unique(),
    default=shortlisted_data[shortlisted_data['category'].str.contains('Verified', case=False)]['verified_source'].sort_values().unique()
)

verified_contacts = data.query(
    "verified_source == @verified_source and @start_date <= date <= @end_date"
).reset_index(drop=True)

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
    options=shortlisted_data['sync_source'].drop_duplicates().dropna().sort_values(),
    default=shortlisted_data['sync_source'].drop_duplicates().dropna().sort_values()
)

# Updates
updates = data.query(
    "sync_source == @sync_source and @start_date <= date <= @end_date and sync_source.notnull()"
).reset_index(drop=True)

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
verified_emails = verified_contacts[verified_contacts['category'] == 'Verified Email'].groupby('date').nunique()['parent_id']
verified_emails = verified_emails.resample('M').sum().reset_index()
verified_emails['date'] = verified_emails['date'].dt.strftime('%b\'%y')
verified_emails.rename(columns={'parent_id': 'Emails'}, inplace=True)

verified_phone = verified_contacts[verified_contacts['category'] == 'Verified Phone'].groupby('date').nunique()['parent_id']
verified_phone = verified_phone.resample('M').sum().reset_index()
verified_phone['date'] = verified_phone['date'].dt.strftime('%b\'%y')
verified_phone.rename(columns={'parent_id': 'Phones'}, inplace=True)

merged_df = pd.merge(verified_emails, verified_phone, on='date', how='outer')

st.markdown('###')
st.markdown('##### Monthly Trend')
fig = px.line(merged_df, x='date', y=['Emails', 'Phones'], width=None, line_shape='spline')
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
    margin=dict(l=0, r=0, t=70, b=0)
)
st.plotly_chart(fig, use_container_width=True, config=plotly_config)

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
line_chart_data = updates.groupby([pd.Grouper(key='date', freq='M'), 'update_type']).size().reset_index(name='count')
line_chart_data['date'] = line_chart_data['date'].dt.strftime('%b\'%y')

line_chart = px.line(line_chart_data, x='date', y='count', color='update_type', width=None, line_shape='spline')
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
    margin=dict(l=0, r=0, t=70, b=0)
)
st.plotly_chart(line_chart, use_container_width=True, config=plotly_config)

st.markdown("""---""")

# Row D
st.markdown('## Data Update Breakdown')

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
    th:first-child, td:first-child {
        width: 25%;
    }
    th:last-child, td:last-child {
        width: 75%;
    }
    tr:hover {
        background-color: #f5f5f5;
    }
</style>
"""

updates_breakdown = updates.groupby(
    by=['update_type']).nunique()['parent_id'].reset_index().rename(
        columns={
            'update_type': 'Description',
            'parent_id': 'Updates'
        }
    )

updates_breakdown = updates_breakdown.sort_values(by=['Updates'], ascending=False)

st.markdown("##")
st.markdown('##### Updates Breakdown')
col1, col2, col3 = st.columns([2, 0.5, 2])

# CSS to inject contained in a string
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            .streamlit-container {
                width: 100%;
            }
            </style>
            """


# Inject CSS with Markdown
col1.markdown(hide_table_row_index, unsafe_allow_html=True)

col1.table(updates_breakdown.style.format(thousands=','))
col1.write('The reason for the higher number is because for each record there are multiple details (like email or phone number), and each of those data points got updated. So, some records are listed more than once because their information overlaps in multiple rows.')

col2.write(' ')

# Pie Chart
pie_chart = px.pie(updates_breakdown, values='Updates', names='Description', hover_data=['Updates'], title='', color=np.log10(updates_breakdown['Updates']))
pie_chart.update_traces(textposition='outside', textinfo='percent+label')
pie_chart.update_layout(showlegend=False,
                        margin=dict(t=10, b=0, l=0, r=175),
                        # font=dict(size=13)
                        )
col3.plotly_chart(pie_chart, config=plotly_config)

st.markdown("""---""")
st.markdown("##")
st.markdown('##### Email Updates Breakdown')

email_updates_breakdown = updates[(updates['email_type'].notnull()) & (updates['update_type'] == 'Email')].reset_index(drop=True)
email_updates_breakdown = email_updates_breakdown.copy()

email_updates_type_breakdown = email_updates_breakdown.groupby(
    by=['email_type']).nunique()['parent_id'].reset_index().rename(
        columns={
            'email_type': 'Description',
            'parent_id': 'Updates'
        }
    )

email_updates_type_breakdown = email_updates_type_breakdown.sort_values(by=['Description'], ascending=False)

col1, col2, col3 = st.columns([2, 0.5, 2])

# Inject CSS with Markdown
col1.markdown(hide_table_row_index, unsafe_allow_html=True)

col1.table(email_updates_type_breakdown.style.format(thousands=','))

# Create a Sunburst chart

# Group email domains by count and get top 5
top_domains = email_updates_breakdown['email_domain'].value_counts().nlargest(6)

# Replace all other domains with 'Others'
email_updates_breakdown.loc[~email_updates_breakdown['email_domain'].isin(top_domains.index), 'email_domain'] = 'Others'

# Group by email type and email domain, and get unique count of IDs
email_updates_breakdown_grouped = email_updates_breakdown.groupby(
    ['email_type', 'email_domain']
    )['parent_id'].nunique().reset_index().rename(
        columns={
            'email_type': 'Description',
            'email_domain': 'Domain',
            'parent_id': 'Count'
        }
    )

# Create Sunburst chart
email_updates_breakdown_fig = px.sunburst(
    email_updates_breakdown_grouped,
    path=['Description', 'Domain'],
    values='Count'
)

email_updates_breakdown_fig.update_layout(showlegend=True,
                        margin=dict(t=0, b=0, l=0, r=175),
                        font=dict(size=13)
                        )

col3.plotly_chart(email_updates_breakdown_fig, config=plotly_config)

# Define the sorting order
order = {'Others': 0}

# Sort the DataFrame
email_updates_breakdown_grouped['sorting_value'] = email_updates_breakdown_grouped['Domain'].map(order)
email_updates_breakdown_grouped['sorting_value'].fillna(1, inplace=True)
email_updates_breakdown_grouped.sort_values(['Description', 'sorting_value', 'Count'], ascending=[False, False, False], inplace=True)
email_updates_breakdown_grouped.drop(columns=['sorting_value'], inplace=True)

col1.write('###')
col1.table(email_updates_breakdown_grouped.style.format(thousands=','))
col2.write(' ')
st.write('The increased count is due to the fact that multiple email address type(s) got updated for each record and hence it is counted more than once.')