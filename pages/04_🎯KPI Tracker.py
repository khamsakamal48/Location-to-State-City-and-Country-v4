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
@st.cache_data()
def get_data():
    # Attributes List
    df1 = pd.read_parquet('Databases/Custom Fields')
    df1['date'] = pd.to_datetime(df1['date'])

    # Reset the index so that the date column becomes a regular column
    df1 = df1.reset_index(drop=True)

    # Email List
    df2 = pd.read_parquet('Databases/System Record IDs')
    df2 = df2.sort_values(
        by=['constituent_id', 'primary', 'type'],
        ascending=[True, False, True]
    ).copy()

    df2 = df2.drop_duplicates('constituent_id').copy()

    df2 = df2.dropna().reset_index(drop=True).copy()

    # All Alums
    df3 = pd.read_parquet('Databases/All Alums.parquet')

    list_1 = df3['id'].astype(int).to_list()

    # Deceased list
    df4 = pd.read_parquet('Databases/All Constituents.parquet')
    list_2 = df4[
        df4['deceased'] == 'True'
    ]['id'].astype(int).to_list()

    # Inactive list
    list_3 = df4[
        df4['inactive'] == 'True'
    ]['id'].astype(int).to_list()

    # Getting list of opt-outs
    df5 = pd.read_parquet('Databases/Opt-outs.parquet')
    list_4 = df5['id'].astype(int).to_list()

    return df1, df2, list_1, list_2, list_3, list_4

data, email_list, alum_list, deceased_list, inactive_list, opt_outs = get_data()

# ---- SIDEBAR ----
st.sidebar.header('Filters')
## Create a sidebar filter for date range
start_date = st.sidebar.date_input("Start date", value=data['date'].min())
end_date = st.sidebar.date_input("End date", value=data['date'].max())

start_date = pd.Timestamp(start_date)
end_date = pd.Timestamp(end_date)

# Shortlist only Alums in shortlisted data
only_alums = st.sidebar.checkbox('Only Alums?')
if only_alums:
    data = data[data['parent_id'].isin(alum_list)].reset_index(drop=True).copy()

# Shortlist non-deceased (alive) constituents only
ignore_deceased = st.sidebar.checkbox('Ignore deceased constituents?')
if ignore_deceased:
    data = data[~data['parent_id'].isin(deceased_list)].reset_index(drop=True).copy()

# Shortlist active constituents only
ignore_inactive = st.sidebar.checkbox('Ignore non-active constituents?')
if ignore_inactive:
    data = data[~data['parent_id'].isin(inactive_list)].reset_index(drop=True).copy()

# Shortlist non-opted out constituents only
ignore_opt_outs= st.sidebar.checkbox('Ignore opted-out constituents?')
if ignore_opt_outs:
    data = data[~data['parent_id'].isin(opt_outs)].reset_index(drop=True).copy()

# Shortlist data based on Date
shortlisted_data = data[data['date'].between(start_date, end_date)].reset_index(drop=True).copy()

# Get various sources
verified_source = shortlisted_data[
    (shortlisted_data['category'].str.contains('Verified', case=False)) &
    (shortlisted_data['verified_source'] != '')
]['verified_source'].dropna().drop_duplicates().sort_values().reset_index(drop=True)
sync_source = shortlisted_data['sync_source'].drop_duplicates().dropna().sort_values().reset_index(drop=True)

# Combine different sources to one
sources = st.sidebar.multiselect(
    "Select the sources:",
    options=pd.concat([verified_source, sync_source]).drop_duplicates().reset_index(drop=True),
    default=pd.concat([verified_source, sync_source]).drop_duplicates().reset_index(drop=True)
)

# Get Verified contact details
verified_contacts = data[(data['date'].between(start_date, end_date)) & (data['verified_source'].isin(sources))].reset_index(drop=True)

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

# Updates
updates = data[(data['date'].between(start_date, end_date)) & (data['sync_source'].isin(sources))].reset_index(drop=True)

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
verified_emails = verified_emails.rename(columns={'parent_id': 'Emails'}).copy()

verified_phone = verified_contacts[verified_contacts['category'] == 'Verified Phone'].groupby('date').nunique()['parent_id']
verified_phone = verified_phone.resample('M').sum().reset_index()
verified_phone['date'] = verified_phone['date'].dt.strftime('%b\'%y')
verified_phone = verified_phone.rename(columns={'parent_id': 'Phones'}).copy()

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

# Verified Email Address by Source Table
verified_email_address = shortlisted_data[
    (shortlisted_data['category'] == 'Verified Email') &
    (shortlisted_data['verified_source'].isin(sources))
].copy()
verified_email_address = verified_email_address.sort_values(['parent_id', 'verified_source_category', 'email_domain_category']).reset_index(drop=True).copy()
verified_email_address = verified_email_address[['parent_id', 'verified_source_category', 'email_domain_category']].drop_duplicates('parent_id').reset_index(drop=True).copy()
verified_by_source = verified_email_address.groupby(['verified_source_category']).agg({'parent_id': 'count'}).reset_index().rename(columns={
    'verified_source_category': 'Source',
    'parent_id': 'Alum Count'
})
verified_by_source['Source'] = verified_by_source['Source'].apply(lambda x: x.split(' - ')[1])
verified_by_source['Alum Count'] = verified_by_source['Alum Count'].apply(lambda x: "{:,}".format(x))

# Verified Emails by Domain Table
verified_by_domain = verified_email_address.groupby(['email_domain_category']).agg({'parent_id': 'count'}).reset_index().rename(columns={
    'email_domain_category': 'Domain',
    'parent_id': 'Alum Count'
})
verified_by_domain['Domain'] = verified_by_domain['Domain'].apply(lambda x: x.split(' - ')[1])
verified_by_domain['Alum Count'] = verified_by_domain['Alum Count'].apply(lambda x: "{:,}".format(x))

# Figure
combined_verified = verified_email_address.groupby(['verified_source_category', 'email_domain_category']).agg({'parent_id': 'count'}).reset_index().rename(columns={
    'verified_source_category': 'Source',
    'email_domain_category': 'Domain',
    'parent_id': 'Alum Count'
}).copy()
combined_verified['Source'] = combined_verified['Source'].apply(lambda x: x.split(' - ')[1])
combined_verified['Domain'] = combined_verified['Domain'].apply(lambda x: x.split(' - ')[1])

st.markdown('##')
st.markdown('##### Verified Email Addresses')
col9, col10 = st.columns([1, 2])

with col9:
    col9.write('By source')
    col9.dataframe(verified_by_source, hide_index=True, use_container_width=True)
    # col9.markdown('##')
    col9.write('By Domain')
    col9.dataframe(verified_by_domain, hide_index=True, use_container_width=True)

with col10:
    # Create Sunburst chart
    verified_email_updates_breakdown_fig = px.sunburst(
        combined_verified,
        path=['Source', 'Domain'],
        values='Alum Count',
        hover_data=['Alum Count'],
    )

    # Format the hover text to show percentages
    verified_email_updates_breakdown_fig.update_traces(
        hovertemplate='<b>%{label}:</b> %{value} (%{percentParent})',
        textinfo='label+percent parent',  # Show label and percentage of parent on chart
        insidetextorientation='radial'  # Orient text radially inside wedges
    )

    verified_email_updates_breakdown_fig.update_layout(
        showlegend=True,
        font=dict(size=15),
        autosize=False,
        height=550
    )

    col10.plotly_chart(verified_email_updates_breakdown_fig, config=plotly_config, use_container_width=True)

st.divider()

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
st.markdown('## Data Update Comparison')

data_update_comparison = pd.pivot_table(updates, index=['update_type'], columns=['sync_source'], values='parent_id', aggfunc=pd.Series.nunique)

# Rename column index
data_update_comparison.index.names = ['Updates']

st.dataframe(data_update_comparison, use_container_width=True)

# Stacked Bar Chart
# Convert DataFrame to long format
data_update_comparison_long = pd.melt(data_update_comparison.reset_index(), id_vars=['Updates'], var_name='sync_source', value_name='count')

# Create stacked bar chart using Plotly Express
stacked_bar_chart = px.bar(
    data_update_comparison_long,
    x='sync_source', y='count', color='Updates', barmode='stack'
)

# Add axis labels and title
stacked_bar_chart.update_layout(
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

stacked_bar_chart.update_traces(textposition='auto')

# Show the chart
st.plotly_chart(stacked_bar_chart, use_container_width=True, config=plotly_config)


st.divider()
# Row D
st.markdown('## Data Update Breakdown')

updates_breakdown = updates.groupby(
    by=['update_type']).nunique()['parent_id'].reset_index().rename(
        columns={
            'update_type': 'Description',
            'parent_id': 'Updates'
        }
    )

updates_breakdown = updates_breakdown.sort_values(by=['Updates'], ascending=False)

st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('#### Updates Breakdown')
    updates_breakdown = updates_breakdown.reset_index(drop=True).copy()

    st.dataframe(updates_breakdown, use_container_width=True, hide_index=True)
    st.write('The reason for the higher number is because for each record there are multiple details (like email or phone number), and each of those data points got updated. So, some records are listed more than once because their information overlaps in multiple rows.')

with col2:
    # Pie Chart
    pie_chart = px.pie(updates_breakdown, values='Updates', names='Description', hover_data=['Updates'])
    pie_chart.update_traces(textposition='auto', textinfo='percent+label')
    pie_chart.update_layout(showlegend=False,
                            autosize=False,
                            height=600,
                            font=dict(size=15)
                            )
    col2.plotly_chart(pie_chart, config=plotly_config, use_container_width=True)

st.markdown("""---""")
st.markdown("##")
st.markdown('### Email Data Breakdown')

col11, col12 = st.columns([1, 2])

with col11:
    st.markdown('#### Summary')

    # Domain Group
    email_by_domain_group = email_list[['domain_category', 'constituent_id']].groupby('domain_category').agg(
        {'constituent_id': 'count'}).sort_values('domain_category').reset_index().copy()

    email_by_domain_group = email_by_domain_group.rename(columns={
        'domain_category': 'Domain',
        'constituent_id': 'Alum Count'
    })

    email_by_domain_group['Alum Count'] = email_by_domain_group['Alum Count'].apply(lambda x: '{:,}'.format(x))

    email_by_domain_group['Domain'] = email_by_domain_group['Domain'].apply(lambda x: x.split('-', 1)[1])

    st.dataframe(email_by_domain_group, hide_index=True, use_container_width=True)

    # Domain
    st.markdown('#### By Domain')
    email_by_domain = email_list[['domain', 'constituent_id']].groupby('domain').agg(
        {'constituent_id': 'count'}).sort_values(by=['constituent_id'], ascending=[False]).reset_index().copy()

    email_by_domain = email_by_domain.rename(columns={
        'domain': 'Domain',
        'constituent_id': 'Alum Count'
    })

    email_by_domain['Alum Count'] = email_by_domain['Alum Count'].apply(lambda x: '{:,}'.format(x))

    st.dataframe(email_by_domain, hide_index=True, use_container_width=True)

with col12:
    email_by_domain_group['Alum Count'] = email_by_domain_group['Alum Count'].apply(lambda x: x.replace(',', ''))
    email_by_domain_group['Alum Count'] = email_by_domain_group['Alum Count'].astype(int)

    st.plotly_chart(
        px.pie(
            email_by_domain_group,
            values='Alum Count',
            names='Domain'
        ).update_traces(
            textposition='inside',
            textinfo='percent+label'
        ).update(
            layout_showlegend=False
        ).update_layout(
            autosize=False,
            height=600,
            font=dict(size=15)
        ),
        config=plotly_config,
        use_container_width=True
    )

st.divider()

# email_updates_breakdown = updates[(updates['email_type'].notnull()) & (updates['update_type'] == 'Email')].reset_index(drop=True)
# email_updates_breakdown = email_updates_breakdown.copy()
#
# email_updates_type_breakdown = email_updates_breakdown.groupby(
#     by=['email_type']).nunique()['parent_id'].reset_index().rename(
#         columns={
#             'email_type': 'Description',
#             'parent_id': 'Updates'
#         }
#     )
#
# email_updates_type_breakdown = email_updates_type_breakdown.sort_values(by=['Description'], ascending=False)
#
# col1, col2, col3 = st.columns([2, 0.5, 2])
#
# email_updates_type_breakdown_table = email_updates_type_breakdown.copy().reset_index(drop=True)
# email_updates_type_breakdown_table = email_updates_type_breakdown_table.set_index('Description').copy()
#
# col1.dataframe(email_updates_type_breakdown_table, use_container_width=True)
#
# # Create a Sunburst chart
#
# # Group email domains by count and get top 5
# top_domains = email_updates_breakdown['email_domain'].value_counts().nlargest(5)
#
# # Replace all other domains with 'Others'
# email_updates_breakdown.loc[~email_updates_breakdown['email_domain'].isin(top_domains.index), 'email_domain'] = 'Others'
#
# # Group by email type and email domain, and get unique count of IDs
# email_updates_breakdown_grouped = email_updates_breakdown.groupby(
#     ['email_type', 'email_domain']
#     )['parent_id'].nunique().reset_index().rename(
#         columns={
#             'email_type': 'Description',
#             'email_domain': 'Domain',
#             'parent_id': 'Count'
#         }
#     )
#
# # Create Sunburst chart
# email_updates_breakdown_fig = px.sunburst(
#     email_updates_breakdown_grouped,
#     path=['Description', 'Domain'],
#     values='Count'
# )
#
# email_updates_breakdown_fig.update_layout(showlegend=True,
#                         margin=dict(t=0, b=0, l=0, r=175),
#                         font=dict(size=13)
#                         )
#
# col3.plotly_chart(email_updates_breakdown_fig, config=plotly_config)
#
# # Define the sorting order
# order = {'Others': 0}
#
# # Sort the DataFrame
# email_updates_breakdown_grouped['sorting_value'] = email_updates_breakdown_grouped['Domain'].map(order)
# email_updates_breakdown_grouped = email_updates_breakdown_grouped['sorting_value'].fillna(1).copy()
# # email_updates_breakdown_grouped = email_updates_breakdown_grouped.sort_values(['Description', 'sorting_value', 'Count'], ascending=[False, False, False]).copy()
# email_updates_breakdown_grouped = email_updates_breakdown_grouped.drop(columns=['sorting_value']).copy()
#
# col1.write('###')
#
# email_updates_breakdown_grouped = email_updates_breakdown_grouped.reset_index(drop=True).copy()
# email_updates_breakdown_grouped = email_updates_breakdown_grouped.set_index('Description').copy()
#
# col1.dataframe(email_updates_breakdown_grouped, use_container_width=True)
# col2.write(' ')
# text = 'The increased count is due to the fact that multiple email address type(s) got updated for each record and hence it is counted more than once.'
# st.write(f"<p style='text-align: justify'>{text}</p>", unsafe_allow_html=True)

# Location Updates
# st.markdown("""---""")
# st.markdown("##")
# st.markdown('##### Location Updates Breakdown')

# location_updates = updates[updates['update_type'] == 'Location'].reset_index(drop=True)

# st.dataframe(location_updates.head())
st.divider()
if st.sidebar.button('Clear cached data for the dashboard'):
    # Clear values from *all* all in-memory and on-disk data caches:
    # i.e. clear values from both square and cube
    st.cache_data.clear()