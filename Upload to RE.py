import requests
import os
import json
import glob
import smtplib
import ssl
import re
import imaplib
import datetime
import logging
import pandas as pd
import numpy as np

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from jinja2 import Environment
from datetime import datetime
from datetime import time
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

def set_current_directory():
    
    os.chdir(os.getcwd())

def start_logging():
    
    global process_name
    
    # Get File Name of existing script
    process_name = os.path.basename(__file__).replace('.py', '').replace(' ', '_')
    
    logging.basicConfig(filename=f'Logs/{process_name}.log', format='%(asctime)s %(message)s', filemode='w', level=logging.DEBUG)
    
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
    
    global RE_API_KEY, MAIL_USERN, MAIL_PASSWORD, IMAP_URL, IMAP_PORT, SMTP_URL, SMTP_PORT, SEND_TO, FORM_URL

    load_dotenv()

    RE_API_KEY = os.getenv('RE_API_KEY')
    MAIL_USERN = os.getenv('MAIL_USERN')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    IMAP_URL = os.getenv('IMAP_URL')
    IMAP_PORT = os.getenv('IMAP_PORT')
    SMTP_URL = os.getenv('SMTP_URL')
    SMTP_PORT = os.getenv('SMTP_PORT')
    SEND_TO  = os.getenv('SEND_TO')
    FORM_URL = os.getenv('FORM_URL')

def send_error_emails(subject):
    logging.info('Sending email for an error')
    
    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = MAIL_USERN
    message["To"] = SEND_TO

    # Adding Reply-to header
    message.add_header('reply-to', MAIL_USERN)
        
    TEMPLATE="""
    <table style="background-color: #ffffff; border-color: #ffffff; width: auto; margin-left: auto; margin-right: auto;">
    <tbody>
    <tr style="height: 127px;">
    <td style="background-color: #363636; width: 100%; text-align: center; vertical-align: middle; height: 127px;">&nbsp;
    <h1><span style="color: #ffffff;">&nbsp;Raiser's Edge Automation: {{job_name}} Failed</span>&nbsp;</h1>
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
    <td style="background-color: #ff8e2d; width: 50%; text-align: center; vertical-align: middle;">&nbsp;{{job_name}}&nbsp;</td>
    </tr>
    <tr>
    <td style="width: 50%; text-align: center; vertical-align: middle;">&nbsp;<span style="color: #ffffff;">Failed on :</span>&nbsp;</td>
    <td style="background-color: #ff8e2d; width: 50%; text-align: center; vertical-align: middle;">&nbsp;{{current_time}}&nbsp;</td>
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
    <td style="height: 217.34375px; background-color: #f8f9f9; width: 100%; text-align: left; vertical-align: middle;">{{error_log_message}}</td>
    </tr>
    </tbody>
    </table>
    """

    # Create a text/html message from a rendered template
    emailbody = MIMEText(
        Environment().from_string(TEMPLATE).render(
            job_name = subject,
            current_time=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            error_log_message = Argument
        ), "html"
    )

    # Add HTML parts to MIMEMultipart message
    # The email client will try to render the last part first
    try:
        message.attach(emailbody)
        attach_file_to_email(message, f'Logs/{process_name}.log')
        emailcontent = message.as_string()
        
    except:
        message.attach(emailbody)
        emailcontent = message.as_string()
    
    # Create secure connection with server and send email
    context = ssl._create_unverified_context()
    with smtplib.SMTP_SSL(SMTP_URL, SMTP_PORT, context=context) as server:
        server.login(MAIL_USERN, MAIL_PASSWORD)
        server.sendmail(
            MAIL_USERN, SEND_TO, emailcontent
        )

    # Save copy of the sent email to sent items folder
    with imaplib.IMAP4_SSL(IMAP_URL, IMAP_PORT) as imap:
        imap.login(MAIL_USERN, MAIL_PASSWORD)
        imap.append('Sent', '\\Seen', imaplib.Time2Internaldate(time.time()), emailcontent.encode('utf8'))
        imap.logout()

def attach_file_to_email(message, filename):
    
    logging.info('Attach file to email')
    
    # Open the attachment file for reading in binary mode, and make it a MIMEApplication class
    with open(filename, "rb") as f:
        file_attachment = MIMEApplication(f.read())
    
    # Add header/name to the attachments    
    file_attachment.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )
    
    # Attach the file to the message
    message.attach(file_attachment)

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
    
    global data
    
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

def find_remaining_data(all_df, partial_df):
    
    logging.info('Identifying missing data between two Panda Dataframes')
    
    global remaining_data
    
    # Merge dataframes A and B based on common columns
    merged_df = pd.merge(all_df, partial_df, how='outer', indicator=True)
    
    # Extract rows from A that are not in B into a new dataframe C
    remaining_data = merged_df.loc[merged_df['_merge'] == 'left_only', all_df.columns]

def check_errors(re_api_response):
    
    logging.info('Checking for exceptions')
    
    error_keywords = ['error', 'failed', 'invalid', 'unauthorized']
    
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
    
    check_errors(re_api_response)

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
    
    check_errors(re_api_response)

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
    
    check_errors(re_api_response)

def api_to_df(response):
    
    logging.info('Loading API response to a DataFrame')
    
    # Load from JSON to pandas
    api_response = pd.json_normalize(response['value'])
    
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

def update_emails(each_row):
    
    logging.info('Proceeding to update Email')
    
    # Get email address list
    email_list = each_row[['System Record ID', 'Email 1', 'Email 2', 'Email 3']].reset_index(drop=True)
    email_list = pd.DataFrame(
    [
        [each_row.loc[0]['System Record ID'], each_row.loc[0]['Email 1']],
        [each_row.loc[0]['System Record ID'], each_row.loc[0]['Email 2']],
        [each_row.loc[0]['System Record ID'], each_row.loc[0]['Email 3']]
    ],columns=['System Record ID','Email'])
    
    # Get RE ID
    constituent_id = int(email_list['System Record ID'][0])
    
    # Get Email address present in RE
    url = f'https://api.sky.blackbaud.com/constituent/v1/constituents/{constituent_id}/emailaddresses'
    params = {}
    
    get_request_re(url, params)
    
    # Load to Dataframe
    re_data = api_to_df(re_api_response).copy()
    
    # Find missing Email Addresses
    missing_values = set(email_list['Email']).difference(set(re_data['address']))
    missing_values = pd.DataFrame(list(missing_values), columns=['Email']).dropna().reset_index(drop=True)
    
    # Get Data source (Limiting to 50 characters)
    source = f"{each_row.loc[0]['Enter the source of your data?'].title()} - Auto | Email"[:50]
    
    # Check if there's any new email address to add and that the existing email address (to be updated) is not empty
    if len(missing_values) == 0 and not pd.isna(each_row.loc[0]['Email 1']):
        
        ## Mark existing email as primary
        email = each_row.loc[0]['Email 1']
        
        email_address_id = int(re_data[re_data['address'] == email].iloc[0]['id'])
        
        url = f'https://api.sky.blackbaud.com/constituent/v1/emailaddresses/{email_address_id}'
        
        params = {
            'primary': True
        }

        patch_request_re(url, params)
        
        # Adding verified tag
        add_tags(email, 'Verified Email', source, constituent_id)
    
    else:
    
        ## Upload Missing Email Address
        i = 0
        for each_row in missing_values.index:
            each_row = missing_values[each_row:]
            
            email = each_row.loc[0][0]
            
            # Type of email
            if '@iitb.ac.in' in email or '@iitbombay.org' in email or '@sjmsom.in' in email:
                email_type = 'IITB Email'
            
            else:
                email_type = 'Email'
            
            if i == 0:
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
            add_tags(email, 'Verified Email', source, constituent_id)

def update_phones(each_row):
    
    logging.info('Proceeding to update Phone Numbers')
    
    # Get phone number list
    phone_1 = each_row.loc[0]['Phone number 1']
    phone_2 = each_row.loc[0]['Phone number 2']
    phone_3 = each_row.loc[0]['Phone number 3']
    
    phone_list = [phone_1, phone_2, phone_3]
    phone_list = [item for item in phone_list if not(pd.isnull(item)) == True]
    phone_list = [str(x) for x in phone_list]
    
    # Get RE ID
    constituent_id = int(each_row.loc[0]['System Record ID'])
    
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
            phones = re.sub("[^0-9]", "",(each_phone['number']))
            re_data.append(phones)
        except:
            pass
    
    # Find missing phone numbers
    # missing_values = set(phone_list['Phone']).difference(set(re_data['number']))
    # missing_values = pd.DataFrame(list(missing_values), columns=['Phone']).dropna().reset_index(drop=True)
    missing_values = []
    for each_phone in phone_list:
        try:
            likely_phone, score = process.extractOne(each_phone, re_data)
            if score < 80:
                missing_values.append(each_phone)
        except:
            missing_values.append(each_phone)
    
    # Making sure that there are no duplicates in the missing list
    if missing_values != []:
        missing_values = [str(x) for x in missing_values]
        missing = list(process.dedupe(missing_values, threshold=80))
        missing_values = missing
    
    # Get Data source (Limiting to 50 characters)
    source = f"{each_row.loc[0]['Enter the source of your data?'].title()} - Auto | Phone"[:50]
    
    # Check if there's any new email address to add and that the existing email address (to be updated) is not empty
    if missing_values == [] and not pd.isna(each_row.loc[0]['Phone number 1']):
        
        # Mark existing phone number as primary
        for each_phone in re_data_unformatted:
            try:
                likely_phone, score = process.extractOne(each_phone, phone_list)
                if score > 80:
                    phone = each_phone
                    break
            except:
                pass
        
        phone_id = int(re_data_complete[re_data_complete['number'] == phone].iloc[0]['id'])
        
        logging.info('I am here')
        
        url = f'https://api.sky.blackbaud.com/constituent/v1/phones/{phone_id}'
        
        params = {
            'primary': True
        }

        patch_request_re(url, params)
        
        # Adding verified tag
        add_tags(phone, 'Verified Phone', source, constituent_id)
    
    else:
    
        ## Upload Missing Phone Numbers
        i = 0
        for phone in missing_values:
            
            if i == 0:
                params = {
                    'number': phone,
                    'constituent_id': constituent_id,
                    'primary': True,
                    'type': 'Mobile'
                }
            
            else:
                params = {
                    'address': phone,
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
            add_tags(phone, 'Verified Phone', source, constituent_id)

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
    
    # Get Excel file from Microsoft Form
    # download_excel(FORM_URL)
    
    # Load file to a Dataframe
    load_data('Form Responses.xlsx')
    form_data = data.drop(columns = ['ID', 'Start time', 'Completion time', 'Email', 'Name'])
    
    # Remove data that's already uploaded
    
    ## Load data that's uploaded
    load_data('Data Uploaded')
    data_uploaded = data.copy()
    
    ## Identify the new data which is yet to be uploaded
    find_remaining_data(form_data, data_uploaded)
    new_data = remaining_data.copy()
    
    # Upload data to RE
    for each_row in new_data.index:
        each_row = new_data[each_row:]
        
        ## Update Email Addresses
        update_emails(each_row)
        
        ## Update Phone Numbers
        update_phones(each_row)
    
    # Create database of file that's aready uploaded
    
    # Report

except Exception as Argument:
    
    logging.error(Argument)
    
    send_error_emails('Error while uploading data to RE | Location to State, City and Country v4')

finally:
    
    # Housekeeping
    housekeeping()
    
    # Stop Logging
    stop_logging()
        
    exit()