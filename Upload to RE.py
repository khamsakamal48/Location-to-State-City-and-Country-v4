import requests
import os
import json
import glob
import re
import datetime
import logging
import time
import random
import string
import msal
import base64
import pandas as pd
import numpy as np

from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from dotenv import load_dotenv
from fuzzywuzzy import process
from nameparser import HumanName
from datetime import date
from datetime import timedelta


def set_current_directory():
    os.chdir(os.getcwd())


def start_logging():
    global process_name

    # Get File Name of existing script
    process_name = os.path.basename(__file__).replace('.py', '').replace(' ', '_')

    logging.basicConfig(filename=f'Logs/{process_name}.log', format='%(asctime)s %(message)s', filemode='w',
                        level=logging.DEBUG)

    # Printing the output to file for debugging
    logging.info('Starting the Script')


def stop_logging():
    logging.info('Stopping the Script')


def housekeeping():
    logging.info('Doing Housekeeping')

    # Housekeeping
    multiple_files = glob.glob('*_RE_*.json')

    # Iterate over the list of filepaths & remove each file.
    logging.info('Removing old JSON files')
    for each_file in multiple_files:
        try:
            os.remove(each_file)
        except:
            pass


def set_api_request_strategy():
    logging.info('Setting API Request strategy')

    global http

    # API Request strategy
    logging.info('Setting API Request Strategy')

    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=['HEAD', 'GET', 'OPTIONS'],
        backoff_factor=10
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount('https://', adapter)
    http.mount('http://', adapter)


def get_env_variables():
    logging.info('Setting Environment variables')

    global RE_API_KEY, O_CLIENT_ID, CLIENT_SECRET, TENANT_ID, FROM, CC_TO, ERROR_EMAILS_TO, SEND_TO, FORM_URL

    load_dotenv()

    RE_API_KEY = os.getenv('RE_API_KEY')
    O_CLIENT_ID = os.getenv('O_CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TENANT_ID = os.getenv('TENANT_ID')
    FROM = os.getenv('FROM')
    SEND_TO = eval(os.getenv('SEND_TO'))
    CC_TO = eval(os.getenv('CC_TO'))
    ERROR_EMAILS_TO = eval(os.getenv('ERROR_EMAILS_TO'))
    FORM_URL = os.getenv('FORM_URL')


def send_error_emails(subject):
    logging.info('Sending email for an error')

    authority = f'https://login.microsoftonline.com/{TENANT_ID}'

    app = msal.ConfidentialClientApplication(
        client_id=O_CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=authority
    )

    scopes = ["https://graph.microsoft.com/.default"]

    result = None
    result = app.acquire_token_silent(scopes, account=None)

    if not result:
        result = app.acquire_token_for_client(scopes=scopes)

        TEMPLATE = """
        <table style="background-color: #ffffff; border-color: #ffffff; width: auto; margin-left: auto; margin-right: auto;">
        <tbody>
        <tr style="height: 127px;">
        <td style="background-color: #363636; width: 100%; text-align: center; vertical-align: middle; height: 127px;">&nbsp;
        <h1><span style="color: #ffffff;">&nbsp;Raiser's Edge Automation: {job_name} Failed</span>&nbsp;</h1>
        </td>
        </tr>
        <tr style="height: 18px;">
        <td style="height: 18px; background-color: #ffffff; border-color: #ffffff;">&nbsp;</td>
        </tr>
        <tr style="height: 18px;">
        <td style="width: 100%; height: 18px; background-color: #ffffff; border-color: #ffffff; text-align: center; vertical-align: middle;">&nbsp;<span style="color: #455362;">This is to notify you that execution of Auto-updating Alumni records has failed.</span>&nbsp;</td>
        </tr>
        <tr style="height: 18px;">
        <td style="height: 18px; background-color: #ffffff; border-color: #ffffff;">&nbsp;</td>
        </tr>
        <tr style="height: 61px;">
        <td style="width: 100%; background-color: #2f2f2f; height: 61px; text-align: center; vertical-align: middle;">
        <h2><span style="color: #ffffff;">Job details:</span></h2>
        </td>
        </tr>
        <tr style="height: 52px;">
        <td style="height: 52px;">
        <table style="background-color: #2f2f2f; width: 100%; margin-left: auto; margin-right: auto; height: 42px;">
        <tbody>
        <tr>
        <td style="width: 50%; text-align: center; vertical-align: middle;">&nbsp;<span style="color: #ffffff;">Job :</span>&nbsp;</td>
        <td style="background-color: #ff8e2d; width: 50%; text-align: center; vertical-align: middle;">&nbsp;{job_name}&nbsp;</td>
        </tr>
        <tr>
        <td style="width: 50%; text-align: center; vertical-align: middle;">&nbsp;<span style="color: #ffffff;">Failed on :</span>&nbsp;</td>
        <td style="background-color: #ff8e2d; width: 50%; text-align: center; vertical-align: middle;">&nbsp;{current_time}&nbsp;</td>
        </tr>
        </tbody>
        </table>
        </td>
        </tr>
        <tr style="height: 18px;">
        <td style="height: 18px; background-color: #ffffff;">&nbsp;</td>
        </tr>
        <tr style="height: 18px;">
        <td style="height: 18px; width: 100%; background-color: #ffffff; text-align: center; vertical-align: middle;">Below is the detailed error log,</td>
        </tr>
        <tr style="height: 217.34375px;">
        <td style="height: 217.34375px; background-color: #f8f9f9; width: 100%; text-align: left; vertical-align: middle;">{error_log_message}</td>
        </tr>
        </tbody>
        </table>
        """

        subject = 'Error while uploading data to RE | Database Update Form-Model'

        # Create a text/html message from a rendered template
        emailbody = TEMPLATE.format(
            job_name=subject,
            current_time=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            error_log_message=Argument
        )

        # Set up attachment data
        with open(f'Logs/{process_name}.log', 'rb') as f:
            attachment_content = f.read()
        attachment_content = base64.b64encode(attachment_content).decode('utf-8')

        if "access_token" in result:

            endpoint = f'https://graph.microsoft.com/v1.0/users/{FROM}/sendMail'

            email_msg = {
                'Message': {
                    'Subject': subject,
                    'Body': {
                        'ContentType': 'HTML',
                        'Content': emailbody
                    },
                    'ToRecipients': get_recipients(ERROR_EMAILS_TO),
                    'CcRecipients': get_recipients(CC_TO),
                    'Attachments': [
                        {
                            '@odata.type': '#microsoft.graph.fileAttachment',
                            'name': f'{process_name}.log',
                            'contentBytes': attachment_content
                        }
                    ]
                },
                'SaveToSentItems': 'true'
            }

            requests.post(
                endpoint,
                headers={
                    'Authorization': 'Bearer ' + result['access_token']
                },
                json=email_msg
            )

        else:
            logging.info(result.get('error'))
            logging.info(result.get('error_description'))
            logging.info(result.get('correlation_id'))


def get_recipients(email_list):
    value = []

    for email in email_list:
        email = {
            'emailAddress': {
                'address': email
            }
        }

        value.append(email)

    return value


def retrieve_token():
    global access_token

    logging.info('Retrieve token for API connections')

    with open('access_token_output.json') as access_token_output:
        data = json.load(access_token_output)
        access_token = data['access_token']


def download_excel(url):
    logging.info('Downloading responses from Microsoft Forms')

    response = requests.get(url)
    open('Databases/Form Responses.xlsx', 'wb').write(response.content)


def load_data(file):
    logging.info('Loading data to Pandas Dataframe')

    # Get extension
    ext = os.path.splitext(file)[1].lower()

    # Excel
    if ext == '.xlsx' or ext == '.xls':

        # Load file to DataFrame
        data = pd.read_excel(f'Databases/{file}')

    # CSV
    elif ext == '.csv':

        # Load file to DataFrame
        data = pd.read_csv(f'Databases/{file}')

    # Parquet
    else:
        # Load file to DataFrame
        data = pd.read_parquet(f'Databases/{file}')

    return data


def find_remaining_data(all_df, partial_df):
    logging.info('Identifying missing data between two Panda Dataframes')

    # Identify data present in all_df but missing in partial_df
    remaining_data = all_df[~all_df['ID'].isin(partial_df['ID'])].copy()

    return remaining_data


def check_errors(re_api_response):
    logging.info('Checking for exceptions')

    error_keywords = ['error', 'failed', 'invalid', 'unauthorized', 'bad request', 'forbidden', 'not found']

    for keyword in error_keywords:
        if keyword in str(re_api_response).lower():
            raise Exception(f'API returned an error: {re_api_response}')


def get_request_re(url, params):
    logging.info('Running GET Request from RE function')

    global re_api_response

    # Retrieve access_token from file
    retrieve_token()

    # Request headers
    headers = {
        'Bb-Api-Subscription-Key': RE_API_KEY,
        'Authorization': 'Bearer ' + access_token,
    }

    re_api_response = http.get(url, params=params, headers=headers).json()

    logging.info(re_api_response)

    # check_errors(re_api_response)

    # Sleep for 5 seconds
    logging.info('Sleeping for 5 seconds')
    time.sleep(5)


def post_request_re(url, params):
    logging.info('Running POST Request to RE function')

    global re_api_response

    # Retrieve access_token from file
    retrieve_token()

    # Request headers
    headers = {
        'Bb-Api-Subscription-Key': RE_API_KEY,
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json',
    }

    re_api_response = http.post(url, params=params, headers=headers, json=params).json()

    logging.info(re_api_response)

    # check_errors(re_api_response)

    # Sleep for 5 seconds
    logging.info('Sleeping for 5 seconds')
    time.sleep(5)


def patch_request_re(url, params):
    logging.info('Running PATCH Request to RE function')

    global re_api_response

    # Retrieve access_token from file
    retrieve_token()

    # Request headers
    headers = {
        'Bb-Api-Subscription-Key': RE_API_KEY,
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }

    re_api_response = http.patch(url, headers=headers, data=json.dumps(params))

    logging.info(re_api_response)

    # check_errors(re_api_response)

    # Sleep for 5 seconds
    logging.info('Sleeping for 5 seconds')
    time.sleep(5)


def add_county(county):
    # counties = 5001
    # States = 5049
    i = 0
    code_table_ids = [5001, 5049]

    for code_table_id in code_table_ids:

        if i == 1:

            now = datetime.datetime.now()

            # Generate either a 2-digit or 3-digit number randomly
            if random.random() < 0.5:
                unique_num = int(now.strftime('%j%H%M%S%f')[:9])
            else:
                unique_num = int(now.strftime('%j%H%M%S%f')[:10])

            # Generate a random suffix character (either an alphabet or a special character)
            suffix_char = random.choice(string.ascii_lowercase + string.digits + '!@#$%^&*()')

            # Concatenate the unique number and the suffix character
            short_description = str(unique_num % 1000) + suffix_char

            if len(short_description) > 3:
                short_description = short_description[1:]

        else:
            short_description = ''

        url = f'https://api.sky.blackbaud.com/nxt-data-integration/v1/re/codetables/{code_table_id}/tableentries'

        params = {
            'long_description': county,
            'short_description': short_description
        }

        # Delete blank values from JSON
        for i in range(10):
            params = del_blank_values_in_json(params.copy())

        post_request_re(url, params)

        i += 1


def del_blank_values_in_json(d):
    """
    Delete keys with the value ``None`` in a dictionary, recursively.

    This alters the input so you may wish to ``copy`` the dict first.
    """
    # For Python 3, write `list(d.items())`; `d.items()` won’t work
    # For Python 2, write `d.items()`; `d.iteritems()` won’t work
    for key, value in list(d.items()):
        if value == "" or value == {} or value == [] or value == [""]:
            del d[key]
        elif isinstance(value, dict):
            del_blank_values_in_json(value)
    return d


def api_to_df(response):
    logging.info('Loading API response to a DataFrame')

    # Load from JSON to pandas
    try:
        api_response = pd.json_normalize(response['value'])
    except:
        try:
            api_response = pd.json_normalize(response)
        except:
            api_response = pd.json_normalize(response, 'value')

    # Load to a dataframe
    df = pd.DataFrame(data=api_response)

    return df


def add_tags(source, tag, update, constituent_id):
    logging.info('Adding Tags to constituent record')

    params = {
        'category': tag,
        'comment': update,
        'parent_id': constituent_id,
        'value': source,
        'date': datetime.now().replace(microsecond=0).isoformat()
    }

    url = 'https://api.sky.blackbaud.com/constituent/v1/constituents/customfields'

    post_request_re(url, params)


def update_emails(each_row, constituent_id):
    logging.info('Proceeding to update Email')

    # Convert all values to lower-case
    each_row = each_row.map(lambda x: x.lower() if isinstance(x, str) else x)

    # Get email address list
    email_list = each_row[['Email 1', 'Email 2', 'Email 3']].T
    email_list.columns = ['Email']
    email_list = email_list[['Email']].reset_index(drop=True).dropna()

    # Convert all values to lower-case
    email_list = email_list.map(lambda x: x.lower() if isinstance(x, str) else x)

    # Get Email address present in RE
    url = f'https://api.sky.blackbaud.com/constituent/v1/constituents/{constituent_id}/emailaddresses'
    params = {}

    get_request_re(url, params)

    # Load to Dataframe
    re_data = api_to_df(re_api_response).copy()

    # Get emails in RE
    try:
        # Convert all values to lower-case
        re_data = re_data.map(lambda x: x.lower() if isinstance(x, str) else x)

        re_email = re_data[['address']]
        re_email.columns = ['Email']

        # Convert all values to lower-case
        re_email = re_email.map(lambda x: x.lower() if isinstance(x, str) else x)

        # Find missing Email Addresses
        merged_df = pd.merge(email_list, re_email, how='outer', indicator=True)
        missing_values = merged_df.loc[merged_df['_merge'] == 'left_only', email_list.columns]

        missing_values = pd.DataFrame(missing_values).reset_index(drop=True)

    except:
        missing_values = pd.DataFrame(email_list).reset_index(drop=True)

    # Get Data source (Limiting to 50 characters)
    source = f"{each_row['Enter the source of your data?'][0].title().replace('-', '_')} - Auto | Email"[:50]

    # Check if there's any new email address to add and that the existing email address (to be updated) is not empty and that the source is not Live Alumni
    if len(missing_values) == 0 and not pd.isna(each_row.loc[0]['Email 1']) and \
            each_row['Enter the source of your data?'][0].title() != 'Live Alumni':

        ## Mark existing email as primary
        email = each_row['Email 1'][0]

        email_address_id = int(re_data[re_data['address'] == email]['id'].reset_index(drop=True)[0])

        url = f'https://api.sky.blackbaud.com/constituent/v1/emailaddresses/{email_address_id}'

        params = {
            'primary': True
        }

        patch_request_re(url, params)

        # Adding verified tag
        add_tags(email, 'Verified Email', source, constituent_id)

    else:

        if len(missing_values) == 1:
            email = str(missing_values['Email'][0])

            # Type of email
            if '@iitb.ac.in' in email or '@iitbombay.org' in email or '@sjmsom.in' in email:
                email_type = 'IITB Email'

            else:
                email_type = 'Email'

            # Check if the source is Live Alumni
            if each_row['Enter the source of your data?'][0].title() == 'Live Alumni':

                params = {
                    'address': email,
                    'constituent_id': constituent_id,
                    'type': email_type
                }

            else:
                params = {
                    'address': email,
                    'constituent_id': constituent_id,
                    'primary': True,
                    'type': email_type
                }

            url = 'https://api.sky.blackbaud.com/constituent/v1/emailaddresses'

            # Upload to RE
            post_request_re(url, params)

            # Upload Tags

            ## Update Tags
            add_tags(source, 'Sync source', email, constituent_id)

            ## Verified Tags
            if each_row['Enter the source of your data?'][0].title() != 'Live Alumni':
                add_tags(email, 'Verified Email', source, constituent_id)

        else:

            ## Upload Missing Email Address
            i = 0
            for index, row in missing_values.iterrows():
                row = pd.DataFrame(row).T.reset_index(drop=True)

                email = str(row['Email'][0])

                # Type of email
                if '@iitb.ac.in' in email or '@iitbombay.org' in email or '@sjmsom.in' in email:
                    email_type = 'IITB Email'

                else:
                    email_type = 'Email'

                if i == 0 and 'Live Alumni' not in source:
                    params = {
                        'address': email,
                        'constituent_id': constituent_id,
                        'primary': True,
                        'type': email_type
                    }

                else:
                    params = {
                        'address': email,
                        'constituent_id': constituent_id,
                        'type': email_type
                    }

                url = 'https://api.sky.blackbaud.com/constituent/v1/emailaddresses'

                # Upload to RE
                post_request_re(url, params)

                i += 1

                # Upload Tags

                ## Update Tags
                add_tags(source, 'Sync source', email, constituent_id)

                ## Verified Tags
                if 'Live Alumni' not in source:
                    add_tags(email, 'Verified Email', source, constituent_id)


def update_event(row, re_id):
    logging.info('Proceeding to update Phone Numbers')

    if row.loc[0]['Is an Event?'] == 'Yes':

        event_date = row.loc[0]['Event Date']
        event_date = pd.to_datetime(event_date).isoformat()

        params = {
            'category': 'Events Attended',
            'comment': f'Updated on {datetime.now()}'[:50],
            'parent_id': re_id,
            'value': row.loc[0]['Enter the source of your data?'][:50],
            'date': event_date
        }

        url = 'https://api.sky.blackbaud.com/constituent/v1/constituents/customfields'

        post_request_re(url, params)


def update_phones(each_row, constituent_id):
    logging.info('Proceeding to update Phone Numbers')

    # Get phone number list
    phone_1 = each_row.loc[0]['Phone number 1']
    phone_2 = each_row.loc[0]['Phone number 2']
    phone_3 = each_row.loc[0]['Phone number 3']

    phone_list = [phone_1, phone_2, phone_3]
    phone_list = [item for item in phone_list if not (pd.isnull(item)) == True]
    phone_list = [str(x) for x in phone_list]

    # Get Phone Numbers present in RE
    url = f'https://api.sky.blackbaud.com/constituent/v1/constituents/{constituent_id}/phones'
    params = {}

    get_request_re(url, params)

    # Load to a list
    re_data_complete = api_to_df(re_api_response).copy()
    re_data = []
    re_data_unformatted = []
    for each_phone in re_api_response['value']:
        try:
            phones = each_phone['number']
            re_data_unformatted.append(phones)
            phones = re.sub("[^0-9]", "", (each_phone['number']))
            re_data.append(phones)
        except:
            pass

    # Find missing phone numbers
    missing_values = []
    for each_phone in phone_list:
        try:
            likely_phone, score = process.extractOne(each_phone, re_data)
            if score <= 80:
                missing_values.append(each_phone)
        except:
            missing_values.append(each_phone)

    # Making sure that there are no duplicates in the missing list
    if missing_values != []:
        missing_values = [str(x) for x in missing_values]
        missing = list(process.dedupe(missing_values, threshold=80))
        missing_values = missing

    # Get Data source (Limiting to 50 characters)
    source = f"{each_row.loc[0]['Enter the source of your data?'].title().replace('-', '_')} - Auto | Phone"[:50]

    # Check if there's any new phone number to add and that the existing phone number (to be updated) is not empty
    if missing_values == [] and not pd.isna(each_row.loc[0]['Phone number 1']) and each_row.loc[0][
        'Enter the source of your data?'].title() != 'Live Alumni':

        logging.info(re_data_unformatted)
        # Mark existing phone number as primary
        for each_phone in re_data_unformatted:
            try:
                likely_phone, score = process.extractOne(each_phone, re_data)
                if score >= 80:
                    phone = each_phone
                    break
            except:
                pass

        phone_id = int(re_data_complete[re_data_complete['number'] == phone]['id'].reset_index(drop=True)[0])

        url = f'https://api.sky.blackbaud.com/constituent/v1/phones/{phone_id}'

        params = {
            'primary': True
        }

        patch_request_re(url, params)

        phone = re.sub("[^0-9]", "", phone)

        # Adding verified tag
        add_tags(phone, 'Verified Phone', source, constituent_id)

    else:

        ## Upload Missing Phone Numbers
        i = 0
        for phone in missing_values:

            try:
                phone = int(float(str(phone)))
            except:
                phone = re.sub("[^0-9]", "", phone)

            if len(str(phone)) != 0:

                if i == 0 and each_row.loc[0]['Enter the source of your data?'].title() != 'Live Alumni':

                    params = {
                        'number': phone,
                        'constituent_id': constituent_id,
                        'primary': True,
                        'type': 'Mobile'
                    }

                else:
                    params = {
                        'number': phone,
                        'constituent_id': constituent_id,
                        'type': 'Mobile'
                    }

                url = 'https://api.sky.blackbaud.com/constituent/v1/phones'

                # Upload to RE
                post_request_re(url, params)

                i += 1

                # Upload Tags
                ## Update Tags
                add_tags(source, 'Sync source', phone, constituent_id)

                ## Verified Tags
                if each_row.loc[0]['Enter the source of your data?'].title() != 'Live Alumni':
                    add_tags(phone, 'Verified Phone', source, constituent_id)


def update_employment(each_row, constituent_id):
    logging.info('Proceeding to update Employment')

    # Get existing relationships in RE

    ## Get relationship from RE
    url = f'https://api.sky.blackbaud.com/constituent/v1/constituents/{constituent_id}/relationships'
    params = {}

    ### API request
    get_request_re(url, params)

    ### Load to DataFrame
    re_data = api_to_df(re_api_response).copy()
    try:
        re_data = re_data[
            ['id', 'constituent_id', 'is_primary_business', 'name', 'reciprocal_type', 'relation_id', 'type',
             'position']]
    except:
        # When there is no orrganisation in RE
        columns = ['id', 'constituent_id', 'is_primary_business', 'name', 'reciprocal_type', 'relation_id', 'type',
                   'position']

        ## Create a dictionary with column names as keys and NaN as values for a single row
        re_data = {column: [np.nan] for column in columns}

        ## Create a DataFrame using the dictionary
        re_data = pd.DataFrame(re_data)

    ### Get list of employees in RE
    re_employer_list = re_data['name'].to_list()

    ### Drop NaN values
    re_employer_list = [item for item in re_employer_list if not (pd.isnull(item)) == True]

    # Get the new data
    employee_details = each_row[['Organization Name', 'Position', 'Start Date', 'End Date']].reset_index(
        drop=True).fillna('').replace('NA', '').replace('na', '').replace('Other', '').replace('other', '').replace(0,
                                                                                                                    '')
    employee_list = employee_details['Organization Name'].to_list()

    ### Drop NaN values
    employee_list = [item for item in employee_list if not (pd.isnull(item)) == True]

    # Find Org names that have to be updated
    missing_values = []
    for each_org in employee_list:
        try:
            likely_org, score = process.extractOne(each_org, re_employer_list)
            if score <= 90:
                missing_values.append(each_org)
        except:
            missing_values.append(each_org)

    # Making sure that there are no duplicates in the missing list
    if missing_values != []:
        missing_values = [str(x) for x in missing_values]
        missing = list(process.dedupe(missing_values, threshold=90))
        missing_values = missing

    # Get Data source (Limiting to 50 characters)
    source = f"{each_row.loc[0]['Enter the source of your data?'].title().replace('-', '_')} - Auto | Employment"[:50]

    # Get dates
    try:
        start_day = int(employee_details.loc[0]['Start Date'].day)
    except:
        start_day = ''

    try:
        start_month = int(employee_details.loc[0]['Start Date'].month)
    except:
        start_month = ''

    try:
        start_year = int(employee_details.loc[0]['Start Date'].year)
    except:
        start_year = ''

    try:
        end_day = int(employee_details.loc[0]['End Date'].day)
    except:
        end_day = ''

    try:
        end_month = int(employee_details.loc[0]['End Date'].month)
    except:
        end_month = ''

    try:
        end_year = int(employee_details.loc[0]['End Date'].year)
    except:
        end_year = ''

    # Check if there's any new organisations to add and that the existing org name (to be updated) is not empty
    if missing_values == [] and not pd.isna(each_row.loc[0]['Organization Name']):

        # Mark existing org as primary
        for each_org in re_employer_list:
            try:
                likely_org, score = process.extractOne(each_org, employee_list)
                if score >= 90:
                    org = each_org
                    break
            except:
                pass

        relationship_id = re_data[re_data['name'] == org]['id'].reset_index(drop=True)[0]

        # Check if designation needs an update
        designation = str(employee_details.loc[0]['Position'])

        re_designation = str(re_data[re_data['id'] == relationship_id].iloc[0]['position'])

        # Update in RE
        url = f'https://api.sky.blackbaud.com/constituent/v1/relationships/{int(relationship_id)}'

        if designation == re_designation:
            designation = ''

        params = {
            'is_primary_business': True,
            'position': designation,
            'start': {
                'd': start_day,
                'm': start_month,
                'y': start_year
            },
            'end': {
                'd': end_day,
                'm': end_month,
                'y': end_year
            }
        }

        # Delete blank values from JSON
        for i in range(10):
            params = del_blank_values_in_json(params.copy())

        if params != {'is_primary_business': True}:
            patch_request_re(url, params)

    else:

        # Upload missing employment details

        ## Check if the new org is not NaN
        empty_values = ['na', 'other']
        if not any(x in str(employee_details.loc[0]['Organization Name']).lower() for x in empty_values) and len(
                str(employee_details.loc[0]['Organization Name'])) != 0 and str(
                employee_details.loc[0]['Organization Name']) != 0:

            # if str(employee_details.loc[0]['Organization Name']) != '' or str(employee_details.loc[0]['Organization Name']) != 'NA' or str(employee_details.loc[0]['Organization Name']) != 'na' or str(employee_details.loc[0]['Organization Name']) != 'Other' or str(employee_details.loc[0]['Organization Name']) != 0:

            url = 'https://api.sky.blackbaud.com/constituent/v1/relationships'

            ## Check if organisation is a University
            school_matches = ['school', 'college', 'university', 'institute', 'iit', 'iim']

            if any(x in str(employee_details.loc[0]['Organization Name']).lower() for x in school_matches):
                relationship = 'University'

            else:
                relationship = 'Employer'

            # Check if position is NA
            if any(x in str(employee_details.loc[0]['Position']).lower() for x in empty_values) or str(
                    employee_details.loc[0]['Position']) == 0 or len(
                    str(employee_details.loc[0]['Position']).strip()) == 0:
                position = ''
            else:
                position = str(employee_details.loc[0]['Position'])[:50]

            params = {
                'constituent_id': constituent_id,
                'relation': {
                    'name': str(employee_details.loc[0]['Organization Name'])[:60],
                    'type': 'Organization'
                },
                'position': position,
                'start': {
                    'd': start_day,
                    'm': start_month,
                    'y': start_year
                },
                'end': {
                    'd': end_day,
                    'm': end_month,
                    'y': end_year
                },
                'type': relationship,
                'reciprocal_type': 'Employee',
                'is_primary_business': True
            }

            # Delete blank values from JSON
            for i in range(10):
                params = del_blank_values_in_json(params.copy())

            ## Update in RE
            post_request_re(url, params)

            ## Update Tags
            add_tags(source, 'Sync Source', str(employee_details.loc[0]['Organization Name'])[:50], constituent_id)


def update_address(each_row, constituent_id):
    logging.info('Proceeding to update Address')

    # Get addresses present in RE
    url = f'https://api.sky.blackbaud.com/constituent/v1/constituents/{constituent_id}/addresses'
    params = {}

    ## API request
    get_request_re(url, params)

    ### Load to DataFrame
    re_data = api_to_df(re_api_response).copy()
    re_data = re_data[['id', 'constituent_id', 'formatted_address']]
    re_data = re_data.replace(to_replace=['\r\n', '\t', '\n'], value=', ', regex=True)
    re_data = re_data.replace(to_replace=['  '], value=' ', regex=True)

    ### Get list of addresses in RE
    re_address_list = re_data['formatted_address'].to_list()

    ### Drop NaN values
    re_address_list = [item for item in re_address_list if not (pd.isnull(item)) == True]

    # Get the new data
    address_data = pd.DataFrame(each_row[['Address Lines', 'City', 'State', 'Country', 'Postal Code']])
    address_data = address_data.reset_index(drop=True).fillna('').replace('NA', '').replace('Other', '').replace('na',
                                                                                                                 '').replace(
        'other', '').replace('0', '').replace('0.0', '')
    address_data['Address'] = address_data['Address Lines'].astype(str) + ' ' + address_data['City'].astype(str) + ' ' + \
                              address_data['State'].astype(str) + ' ' + address_data['Country'].astype(str) + ' ' + \
                              address_data['Postal Code'].astype(str)
    address_data = address_data.replace(to_replace=['\r\n', '\t', '\n'], value=', ', regex=True)
    address_data = address_data.replace(to_replace=['  '], value=' ', regex=True)
    address_list = address_data['Address'].to_list()

    ### Drop NaN values
    address_list = [item for item in address_list if not (pd.isnull(item)) == True]

    # Find Address that have to be updated
    missing_values = []
    if address_list != []:
        for each_address in address_list:
            try:
                likely_org, score = process.extractOne(each_address, re_address_list)
                if score <= 90:
                    missing_values.append(each_address)
            except:
                missing_values.append(each_address)

    # Making sure that there are no duplicates in the missing list
    if missing_values != []:
        missing_values = [str(x) for x in missing_values]
        missing = list(process.dedupe(missing_values, threshold=90))
        missing_values = missing

    # Get Data source (Limiting to 50 characters)
    source = f"{each_row.loc[0]['Enter the source of your data?'].title().replace('-', '_')} - Auto | Address"[:50]

    # Check if there's any new addresses to add and that the existing address (to be updated) is not empty
    if missing_values == [] and not pd.isna(each_row.loc[0]['Address Lines']):

        # Mark existing org as primary
        for each_address in re_address_list:
            try:
                likely_org, score = process.extractOne(each_address, address_list)
                if score >= 90:
                    address = each_address
                    break
            except:
                pass

        address_id = re_data[re_data['formatted_address'] == address]['id'].reset_index(drop=True)[0]

        # Update in RE
        url = f'https://api.sky.blackbaud.com/constituent/v1/addresses/{address_id}'

        params = {
            'preferred': True
        }

        patch_request_re(url, params)

    else:

        # Upload missing address details
        url = 'https://api.sky.blackbaud.com/constituent/v1/addresses'

        each_row.fillna('', inplace=True)

        address_lines = str(address_list[0]).replace(', ', ', \r\n').replace('  ', ' ').replace('.0', '').strip()[:150]
        city = str(each_row['City'][0])
        state = str(each_row['State'][0])
        country = str(each_row['Country'][0])

        try:
            postal_code = int(str(each_row['Postal Code'][0]).replace('.0', ''))
        except:
            postal_code = str(each_row['Postal Code'][0]).replace('.0', '')

        if postal_code == 0:
            postal_code = ''

        # Check if there's any address to add
        if address_lines != '' and city != '' and state != '' and country != '' and postal_code != '':

            # Ignore state for below countries
            if country == 'Mauritius' or country == 'Switzerland' or country == 'France' or country == 'Bahrain':
                state = ''

            params = {
                'address_lines': address_lines,
                'city': city,
                'state': state,
                'county': state,
                'country': country,
                'postal_code': postal_code,
                'constituent_id': constituent_id,
                'type': 'Home',
                'preferred': True
            }

            # Delete blank values from JSON
            for i in range(10):
                params = del_blank_values_in_json(params.copy())

            try:
                post_request_re(url, params)

            except:

                if 'county of value' in str(re_api_response).lower():
                    add_county(state)
                    post_request_re(url, params)
                else:
                    raise Exception(f'API returned an error: {re_api_response}')

            ## Update Tags
            add_tags(source, 'Sync source', str(address_list[0]).replace('.0', '').replace(' 0', '')[:50],
                     constituent_id)


def update_education(each_row, constituent_id):
    logging.info('Proceeding to update Education')

    # Get the new data
    education_details = each_row[['Class of', 'Degree', 'Department', 'Hostel']].reset_index(drop=True)
    education_class_of = int(str(education_details['Class of'][0]).replace('NA', '0').replace('\xa0', '0'))
    education_degree = str(education_details['Degree'][0]).replace('0', '').replace('NA', '').replace('\xa0', '')
    education_department = str(education_details['Department'][0]).replace('nan', '').replace('NA', '').replace('0',
                                                                                                                '').replace(
        '\xa0', '')
    education_hostel = str(education_details['Hostel'][0]).replace('[', '').replace('"', '').replace(']', '').replace(
        'NA', '').replace('\xa0', '')

    # Check if there's any new education Data to update
    if education_class_of != 0 and education_degree != '' and education_department != '' and education_hostel != '':

        # Get education present in RE
        url = f'https://api.sky.blackbaud.com/constituent/v1/constituents/{constituent_id}/educations'
        params = {}

        get_request_re(url, params)

        # Load to a dataframe
        re_data = api_to_df(re_api_response).copy()

        # Cases when no education exists in RE
        try:
            re_data = re_data[re_data['school'] == 'Indian Institute of Technology Bombay'].reset_index(drop=True)

            # Check if number of educations in RE
            if len(re_data) == 1:

                education_id = int(re_data['id'][0])

                try:
                    re_class_of = int(re_data['class_of'][0])
                except:
                    re_class_of = 0

                try:
                    re_degree = str(re_data['degree'][0])
                except:
                    re_degree = ''

                try:
                    re_department = str(re_data['majors'][0][2:-2])
                except:
                    re_department = ''

                try:
                    re_hostel = str(re_data['social_organization'][0])
                except:
                    re_hostel = ''

                # Get Data source (Limiting to 50 characters)
                source = f"{each_row.loc[0]['Enter the source of your data?'].title().replace('-', '_')} - Auto | Education"[
                         :50]

                # Get current year
                current_year = datetime.now().strftime("%Y")

                # All values as empty
                class_of = ''
                degree = ''
                department = ''
                hostel = ''

                if not (1962 <= int(re_class_of) <= int(current_year)):

                    class_of = education_class_of

                    # Degree
                    degree_df = pd.read_parquet('Databases/Degrees')

                    if re_degree == 'Other' or re_degree == '':
                        degree = degree_df[degree_df['Form Degrees'] == education_degree].reset_index(drop=True).loc[0][
                            1]

                    # Department
                    if re_department == '' or re_department == 'Other':
                        department = education_department

                    if re_hostel == 'Other' or re_hostel == '':
                        hostel = education_hostel

                    params = {
                        'class_of': class_of,
                        'date_graduated': {
                            'y': class_of
                        },
                        'date_left': {
                            'y': class_of
                        },
                        'degree': degree,
                        'majors': [
                            department
                        ],
                        'social_organization': hostel
                    }

                    # Delete blank values from JSON
                    for i in range(10):
                        params = del_blank_values_in_json(params.copy())

                    # Check if there any data to upload
                    if params != {}:
                        url = f'https://api.sky.blackbaud.com/constituent/v1/educations/{education_id}'

                        patch_request_re(url, params)

                        # Add Tags
                        add_tags(source, 'Sync source', str(params)[:50], constituent_id)

                elif re_class_of == education_class_of:

                    class_of = ''

                    # Degree
                    degree_df = pd.read_parquet('Databases/Degrees')

                    if re_degree == 'Other' or re_degree == '':
                        degree = degree_df[degree_df['Form Degrees'] == education_degree].reset_index(drop=True).loc[0][
                            1]

                    # Department
                    if re_department == '' or re_department == 'Other':
                        department = education_department

                    if re_hostel == 'Other' or re_hostel == '':
                        hostel = education_hostel

                    params = {
                        'class_of': class_of,
                        'date_graduated': {
                            'y': class_of
                        },
                        'date_left': {
                            'y': class_of
                        },
                        'degree': degree,
                        'majors': [
                            department
                        ],
                        'social_organization': hostel
                    }

                    # Delete blank values from JSON
                    for i in range(10):
                        params = del_blank_values_in_json(params.copy())

                    logging.info(params)

                    # Check if there any data to upload
                    if params != {}:
                        url = f'https://api.sky.blackbaud.com/constituent/v1/educations/{education_id}'

                        patch_request_re(url, params)

                        # Add Tags
                        add_tags(source, 'Sync source', str(params)[:50], constituent_id)

                else:
                    # Different education exists than what's provided
                    re_data_html = re_data.to_html(index=False, classes='table table-stripped')
                    each_row_html = each_row.to_html(index=False, classes='table table-stripped')
                    send_mail_different_education(re_data_html, each_row_html,
                                                  'Different education data exists in RE and the one provided by Alum')

            else:

                # Multiple education exists than what's provided
                re_data_html = re_data.to_html(index=False, classes='table table-stripped')
                each_row_html = each_row.to_html(index=False, classes='table table-stripped')
                send_mail_different_education(re_data_html, each_row_html, 'Multiple education data exists in RE')

        except:
            # When no education exists in RE

            # Degree
            degree_df = pd.read_parquet('Databases/Degrees')

            # Get Data source (Limiting to 50 characters)
            source = f"{each_row.loc[0]['Enter the source of your data?'].title().replace('-', '_')} - Auto | Education"[
                     :50]

            params = {
                'constituent_id': constituent_id,
                'school': 'Indian Institute of Technology Bombay',
                'class_of': education_class_of,
                'date_graduated': {
                    'y': education_class_of
                },
                'date_left': {
                    'y': education_class_of
                },
                'degree': degree_df[degree_df['Form Degrees'] == education_degree].reset_index(drop=True).loc[0][1],
                'majors': [
                    education_department
                ],
                'social_organization': education_hostel,
                'status': 'Graduated',
                'primary': True
            }

            logging.info(params)

            # Delete blank values from JSON
            for i in range(10):
                params = del_blank_values_in_json(params.copy())

            url = 'https://api.sky.blackbaud.com/constituent/v1/educations'

            post_request_re(url, params)

            # Add Tags
            add_tags(source, 'Sync source', str(params)[:50], constituent_id)


def send_mail_different_education(re_data, each_row, subject):
    logging.info('Sending email for different education')

    authority = f'https://login.microsoftonline.com/{TENANT_ID}'

    app = msal.ConfidentialClientApplication(
        client_id=O_CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=authority
    )

    scopes = ["https://graph.microsoft.com/.default"]

    result = None
    result = app.acquire_token_silent(scopes, account=None)

    if not result:
        result = app.acquire_token_for_client(scopes=scopes)

        TEMPLATE = """
        <p>Hi,</p>
        <p>This is to inform you that the Education data provided by Alum is different than that exists in Raisers Edge.</p>
        <p><a href="https://host.nxt.blackbaud.com/constituent/records/{constituent_id}?envId=p-dzY8gGigKUidokeljxaQiA&amp;svcId=renxt" target="_blank"><strong>Open in RE</strong></a></p>
        <p>&nbsp;</p>
        <p>Below is the data for your comparison:</p>
        <h3>Raisers Edge Data:</h3>
        <p>{re_data}</p>
        <p>&nbsp;</p>
        <h3>Provided by Alum:</h3>
        <p>{education_data}</p>
        <p>&nbsp;</p>
        <p>Thanks &amp; Regards</p>
        <p>A Bot.</p>
        """

        # Create a text/html message from a rendered template
        emailbody = TEMPLATE.format(
            constituent_id=constituent_id,
            re_data=re_data,
            education_data=each_row
        )

        if "access_token" in result:

            endpoint = f'https://graph.microsoft.com/v1.0/users/{FROM}/sendMail'

            email_msg = {
                'Message': {
                    'Subject': subject,
                    'Body': {
                        'ContentType': 'HTML',
                        'Content': emailbody
                    },
                    'ToRecipients': get_recipients(ERROR_EMAILS_TO),
                    'CcRecipients': get_recipients(CC_TO),
                    'SaveToSentItems': 'true'
                }
            }

            requests.post(
                endpoint,
                headers={
                    'Authorization': 'Bearer ' + result['access_token']
                },
                json=email_msg
            )

        else:
            logging.info(result.get('error'))
            logging.info(result.get('error_description'))
            logging.info(result.get('correlation_id'))


def update_name(each_row, constituent_id):
    logging.info('Proceeding to update Names')

    # Get the new data
    name = each_row['Name2'][0]
    name.replace('\r\n', ' ').replace('\t', ' ').replace('\n', ' ').replace('  ', ' ')

    # Get First, Middle and Last Name
    name = HumanName(str(name))
    first_name = str(name.first).title()

    # In case there's no middle name
    try:
        middle_name = str(name.middle).title()
    except:
        middle_name = ''

    last_name = str(name.last).title()
    title = str(name.title).title()

    # Get existing name from RE
    url = f'https://api.sky.blackbaud.com/constituent/v1/constituents/{constituent_id}'
    params = {}

    get_request_re(url, params)

    # Load to a DataFrame
    re_data = api_to_df(re_api_response).copy()

    # When there's no middle name in RE
    try:
        re_data = re_data[['name', 'title', 'first', 'middle', 'last']]
    except:
        re_data = re_data[['name', 'title', 'first', 'last']]

    # RE Data
    re_f_name = re_data['first'][0]

    try:
        re_m_name = re_data['middle'][0]
    except:
        re_m_name = ''

    re_l_name = re_data['last'][0]
    re_title = re_data['title'][0]

    # Check if name needs an update
    if title is np.nan:
        if re_title != title:

            # Name needs an update
            params = {
                'title': str(title),
                'first': str(first_name)[:50],
                'middle': str(middle_name)[:50],
                'last': str(last_name)[:50],
                'former_name': str(
                    str(re_title) + ' ' + str(re_f_name) + ' ' + str(re_m_name) + ' ' + str(re_l_name)).replace('  ',
                                                                                                                ' ')[
                               :100]
            }

            # Delete blank values from JSON
            for i in range(10):
                params = del_blank_values_in_json(params.copy())

            url = f'https://api.sky.blackbaud.com/constituent/v1/constituents/{constituent_id}'

            ## Update in RE
            patch_request_re(url, params)

            ## Update Tags
            source = f"{each_row.loc[0]['Enter the source of your data?'].title().replace('-', '_')} - Auto | Name"[:50]
            add_tags(source, 'Sync Source',
                     str(str(title) + ' ' + str(first_name) + ' ' + str(middle_name) + ' ' + str(last_name))[:50],
                     constituent_id)

            # Send email for different name
            send_mail_different_name(
                str(str(re_title) + ' ' + str(re_f_name) + ' ' + str(re_m_name) + ' ' + str(re_l_name)),
                str(str(title) + ' ' + str(first_name) + ' ' + str(middle_name) + ' ' + str(last_name)),
                'Different name exists in Raisers Edge and the one shared by Alum')
    else:

        if re_f_name != first_name or re_m_name != middle_name or re_l_name != last_name:

            # Name needs an update
            params = {
                'title': str(title),
                'first': str(first_name)[:50],
                'middle': str(middle_name)[:50],
                'last': str(last_name)[:50],
                'former_name': str(
                    str(re_title) + ' ' + str(re_f_name) + ' ' + str(re_m_name) + ' ' + str(re_l_name)).replace('  ',
                                                                                                                ' ')[
                               :100]
            }

            # Delete blank values from JSON
            for i in range(10):
                params = del_blank_values_in_json(params.copy())

            url = f'https://api.sky.blackbaud.com/constituent/v1/constituents/{constituent_id}'

            ## Update in RE
            patch_request_re(url, params)

            ## Update Tags
            source = f"{each_row.loc[0]['Enter the source of your data?'].title().replace('-', '_')} - Auto | Name"[:50]
            add_tags(source, 'Sync Source',
                     str(str(title) + ' ' + str(first_name) + ' ' + str(middle_name) + ' ' + str(last_name))[:50],
                     constituent_id)

            # Send email for different name
            send_mail_different_name(
                str(str(re_title) + ' ' + str(re_f_name) + ' ' + str(re_m_name) + ' ' + str(re_l_name)),
                str(str(title) + ' ' + str(first_name) + ' ' + str(middle_name) + ' ' + str(last_name)),
                'Different name exists in Raisers Edge and the one shared by Alum')


def clean_url(url):
    url = str(url)

    # Remove everything after ?
    sep = '?'
    try:
        url = url.split(sep, 1)[0]
    except:
        pass

    # Remove https://www. and so on
    try:
        url = url.replace('https://www.', '').replace('http://www.', '').replace('www.', '').replace('http://',
                                                                                                     '').replace(
            'https://', '').replace('in.linkedin', 'linkedin')
    except:
        pass

    # Remove / at the end
    try:
        if url[-1] == '/':
            url = url[:-1]
    except:
        pass

    return url


def update_linkedin(each_row, constituent_id):
    logging.info('Proceeding to update LinkedIn')

    # Get the new data
    linkedin = each_row['LinkedIn'][0]

    if 'linkedin' in str(linkedin):
        linkedin = clean_url(linkedin)

        params = {
            'address': linkedin,
            'constituent_id': constituent_id,
            'primary': True,
            'type': 'LinkedIn'
        }

        url = 'https://api.sky.blackbaud.com/constituent/v1/onlinepresences'

        # Update in RE
        post_request_re(url, params)

        ## Update Tags
        source = f"{each_row.loc[0]['Enter the source of your data?'].title().replace('-', '_')} - Auto | Online Presence"[
                 :50]
        add_tags(source, 'Sync Source', linkedin[:50], constituent_id)


def send_mail_different_name(re_name, new_name, subject):
    logging.info('Sending email for different names')

    authority = f'https://login.microsoftonline.com/{TENANT_ID}'

    app = msal.ConfidentialClientApplication(
        client_id=O_CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=authority
    )

    scopes = ["https://graph.microsoft.com/.default"]

    result = None
    result = app.acquire_token_silent(scopes, account=None)

    if not result:
        result = app.acquire_token_for_client(scopes=scopes)

        TEMPLATE = """
        <p>Hi,</p>
        <p>This is to inform you that the name provided by Alum is different than that exists in Raisers Edge.</p>
        <p>The new one has been updated in Raisers Edge, and the Existing name is stored as &#39;<u>Former Name</u>&#39; in RE.</p>
        <p><a href="https://host.nxt.blackbaud.com/constituent/records/{constituent_id}?envId=p-dzY8gGigKUidokeljxaQiA&amp;svcId=renxt" target="_blank"><strong>Open in RE</strong></a></p>
        <table align="left" border="1" cellpadding="1" cellspacing="1" style="width:500px">
            <thead>
                <tr>
                    <th scope="col">Existing Name</th>
                    <th scope="col">New Name</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="text-align:center">{re_name}</td>
                    <td style="text-align:center">{new_name}</td>
                </tr>
            </tbody>
        </table>
        <p>&nbsp;</p>
        <p>&nbsp;</p>
        <p>&nbsp;</p>
        <p>&nbsp;</p>
        <p>Thanks &amp; Regards</p>
        <p>A Bot.</p>
        """

        # Create a text/html message from a rendered template
        emailbody = TEMPLATE.format(
            constituent_id=constituent_id,
            re_name=re_name,
            new_name=new_name
        )

        if "access_token" in result:

            endpoint = f'https://graph.microsoft.com/v1.0/users/{FROM}/sendMail'

            email_msg = {
                'Message': {
                    'Subject': subject,
                    'Body': {
                        'ContentType': 'HTML',
                        'Content': emailbody
                    },
                    'ToRecipients': get_recipients(ERROR_EMAILS_TO),
                    'CcRecipients': get_recipients(CC_TO),
                },
                'SaveToSentItems': 'true'
            }

            requests.post(
                endpoint,
                headers={
                    'Authorization': 'Bearer ' + result['access_token']
                },
                json=email_msg
            )

        else:
            logging.info(result.get('error'))
            logging.info(result.get('error_description'))
            logging.info(result.get('correlation_id'))


def check_if_new(each_row, constituent_id):
    logging.info('Checking if the record is a new record')

    # Get created data based on constituent code
    url = f'https://api.sky.blackbaud.com/constituent/v1/constituents/{constituent_id}/constituentcodes'
    params = {}
    get_request_re(url, params)

    # Load to a DataFrame
    re_data = api_to_df(re_api_response).copy()

    ## Convert to Datetime format
    re_data['date_added'] = pd.to_datetime(re_data['date_added'], utc=True)

    # Sort DataFrame
    re_data.sort_values(by=['date_added'], inplace=True)
    re_data.reset_index(drop=True, inplace=True)

    created_date = re_data['date_added'][0]
    created_date = pd.to_datetime(created_date, format='ISO8601')
    created_date = created_date.date()

    # Get Current Date
    today = date.today()

    # Date 7 Days ago
    start_date = (today - timedelta(days=7))

    if today >= created_date >= start_date:
        # Constituent was recently created

        # Get source
        source = f"{each_row.loc[0]['Enter the source of your data?'].title().replace('-', '_')} - Auto | New Record"[
                 :50]

        comment = re_data.loc[0]['description']

        ## Update Tags
        add_tags(source, 'Sync source', str(comment)[:50], constituent_id)


def issue_with_updates(df, error):
    logging.info('Sending email for failure to update record')

    authority = f'https://login.microsoftonline.com/{TENANT_ID}'

    app = msal.ConfidentialClientApplication(
        client_id=O_CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=authority
    )

    scopes = ["https://graph.microsoft.com/.default"]

    result = None
    result = app.acquire_token_silent(scopes, account=None)

    if not result:
        result = app.acquire_token_for_client(scopes=scopes)

        TEMPLATE = """
            <p>Hi,</p>
            <p>This is to inform you that the we were unable to update below record in Raisers Edge.</p>
            <p><a href="https://host.nxt.blackbaud.com/constituent/records/{constituent_id}?envId=p-dzY8gGigKUidokeljxaQiA&amp;svcId=renxt" target="_blank"><strong>Open in RE</strong></a></p>
            <p>&nbsp;</p>
            <p>Below is the data for your reference:</p>
            <h3>Alumni Data:</h3>
            <p>{re_data}</p>
            <p>&nbsp;</p>
            <h3>Error:</h3>
            <p>{error}</p>
            <p>&nbsp;</p>
            <p>Thanks &amp; Regards</p>
            <p>A Bot.</p>
            """

        # Create a text/html message from a rendered template
        emailbody = TEMPLATE.format(
            constituent_id=constituent_id,
            re_data=df.to_html(index=False),
            error=str(error)
        )

        subject = 'Failure to update record in Raisers Edge | Database Update Workflow'

        # Set up attachment data
        with open(f'Logs/{process_name}.log', 'rb') as f:
            attachment_content = f.read()
        attachment_content = base64.b64encode(attachment_content).decode('utf-8')

        if "access_token" in result:

            endpoint = f'https://graph.microsoft.com/v1.0/users/{FROM}/sendMail'

            email_msg = {
                'Message': {
                    'Subject': subject,
                    'Body': {
                        'ContentType': 'HTML',
                        'Content': emailbody
                    },
                    'ToRecipients': get_recipients(ERROR_EMAILS_TO),
                    'CcRecipients': get_recipients(CC_TO),
                    'Attachments': [
                        {
                            '@odata.type': '#microsoft.graph.fileAttachment',
                            'name': f'{process_name}.log',
                            'contentBytes': attachment_content
                        }
                    ]
                },
                'SaveToSentItems': 'true'
            }

            requests.post(
                endpoint,
                headers={
                    'Authorization': 'Bearer ' + result['access_token']
                },
                json=email_msg
            )

        else:
            logging.info(result.get('error'))
            logging.info(result.get('error_description'))
            logging.info(result.get('correlation_id'))


try:

    # Set current directory
    set_current_directory()

    # Start Logging for Debugging
    start_logging()

    # Retrieve contents from .env file
    get_env_variables()

    # Housekeeping
    housekeeping()

    # Set API Request strategy
    set_api_request_strategy()

    # # Get Excel file from Microsoft Form
    download_excel(FORM_URL)

    # Load file to a Dataframe
    form_data = load_data('Form Responses.xlsx').copy()
    form_data.drop(columns=['Start time', 'Completion time', 'Email', 'Name'], inplace=True)

    # Pre-process the data
    logging.info('Pre-processing data')
    # Replace NA, 0 and Other with NaN
    form_data = form_data.replace(to_replace=[0, 'NA', 'na', 'Other', 'other'], value=np.NaN)

    # Fixing the class of column
    # 1. Replace 'Other' and 'NA' values with NaN
    form_data['Class of'] = pd.to_numeric(form_data['Class of'], errors='coerce')
    # 2. Replace NaN values with a default value, such as -1 or 0
    form_data['Class of'].fillna(0, inplace=True)
    # 3. Convert the 'class_of' column to 'float'
    form_data['Class of'] = form_data['Class of'].astype(float)
    # 4. Convert the 'float' datatype to the 'int' datatype
    form_data['Class of'] = form_data['Class of'].astype(int)

    # Fixing the Postal code column
    # 1. Replace 'Other' and 'NA' values with NaN
    form_data['Postal Code'] = pd.to_numeric(form_data['Postal Code'], errors='coerce')
    # 2. Replace NaN values with a default value, such as -1 or 0
    form_data['Postal Code'].fillna(0, inplace=True)
    # 3. Convert the 'class_of' column to 'float'
    form_data['Postal Code'] = form_data['Postal Code'].astype(float)

    # Remove data that's already uploaded

    # Load data that's uploaded
    try:
        data_uploaded = load_data('Data Uploaded').copy()
    except:
        data_uploaded = pd.DataFrame(columns=form_data.columns)

    # Identify the new data which is yet to be uploaded
    new_data = find_remaining_data(form_data, data_uploaded).copy()

    # Upload data to RE
    for index, each_row in new_data.iterrows():

        each_row = pd.DataFrame(each_row).T.reset_index(drop=True)

        each_row_bak = each_row.copy()

        # Get RE ID
        constituent_id = int(each_row['System Record ID'][0])

        logging.info(f'Proceeding to update record with System Record ID: {constituent_id}')

        try:

            # Update Email Addresses
            update_emails(each_row, constituent_id)

            # Update Phone Numbers
            update_phones(each_row, constituent_id)

            # Update Employment
            update_employment(each_row, constituent_id)

            # Update Address
            update_address(each_row, constituent_id)

            # Update Education
            update_education(each_row, constituent_id)

            # Update Name
            update_name(each_row, constituent_id)

            # Update LinkedIn URL
            update_linkedin(each_row, constituent_id)

            # Check if the record is a new record
            check_if_new(each_row, constituent_id)

            # Checking if it's an event
            update_event(each_row, constituent_id)

            # Sleep for 5 seconds
            logging.info('Sleeping for 5 seconds')
            time.sleep(5)

            # Create database of file that's already uploaded
            logging.info('Updating Database of synced records')
            each_row_bak['Class of'] = pd.to_numeric(each_row_bak['Class of'], errors='ignore')
            data_uploaded = pd.concat([data_uploaded, each_row_bak], axis=0, ignore_index=True)
            data_uploaded = data_uploaded.drop_duplicates('ID').copy()
            data_uploaded.to_parquet('Databases/Data Uploaded', index=False)

        except Exception as Argument:
            # Send email
            issue_with_updates(each_row_bak, Argument)

            # Move on to the next record
            pass

except Exception as Argument:

    logging.error(Argument)

    send_error_emails()

finally:

    # Housekeeping
    housekeeping()

    # Stop Logging
    stop_logging()

    exit()
