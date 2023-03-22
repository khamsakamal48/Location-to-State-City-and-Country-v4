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
import time
import pandas as pd
import numpy as np

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from jinja2 import Environment
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from dotenv import load_dotenv

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
    
    global RE_API_KEY, MAIL_USERN, MAIL_PASSWORD, IMAP_URL, IMAP_PORT, SMTP_URL, SMTP_PORT, SEND_TO

    load_dotenv()

    RE_API_KEY = os.getenv('RE_API_KEY')
    MAIL_USERN = os.getenv('MAIL_USERN')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    IMAP_URL = os.getenv('IMAP_URL')
    IMAP_PORT = os.getenv('IMAP_PORT')
    SMTP_URL = os.getenv('SMTP_URL')
    SMTP_PORT = os.getenv('SMTP_PORT')
    SEND_TO  = os.getenv('SEND_TO')

def send_error_emails(subject, Argument):
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
        f"attachment; filename= {filename.replace('Logs', '')}",
    )
    
    # Attach the file to the message
    message.attach(file_attachment)

def retrieve_token():
    
    global access_token
    
    logging.info('Retrieve token for API connections')
    
    with open('access_token_output.json') as access_token_output:
        data = json.load(access_token_output)
        access_token = data['access_token']

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

def pagination_api_request(url, params):
    
    # Pagination request to retreive list
    while url:
        # Blackbaud API GET request
        get_request_re(url, params)
        
        # Incremental File name
        i = 1
        while os.path.exists(f'API_Response_RE_{process_name}_{i}.json'):
            i += 1
            
        with open(f'API_Response_RE_{process_name}_{i}.json', 'w') as list_output:
            json.dump(re_api_response, list_output,ensure_ascii=False, sort_keys=True, indent=4)
        
        # Check if a variable is present in file
        with open(f'API_Response_RE_{process_name}_{i}.json') as list_output_last:
            
            if 'next_link' in list_output_last.read():
                url = re_api_response['next_link']
                
            else:
                break

def load_from_json_to_parquet():
    
    logging.info('Loading from JSON to Parquet file')
    
    # Get a list of all the file paths that ends with wildcard from in specified directory
    fileList = glob.glob('API_Response_RE_*.json')
    
    df = pd.DataFrame()
    
    for each_file in fileList:
        
        # Open Each JSON File
        with open(each_file, 'r') as json_file:
            
            # Load JSON File
            json_content = json.load(json_file)
            
            # Convert non-string values to strings
            json_content = convert_to_strings(json_content)
            
            # Load to a dataframe
            df_ = api_to_df(json_content)
            
            df = pd.concat([df, df_])
    
    # export from dataframe to parquet
    logging.info('Loading DataFrame to file')
    df.to_parquet('Databases/Custom Fields', index=False)

def convert_to_strings(obj):
    """
    Recursively convert non-string values to strings in a dictionary
    """
    if isinstance(obj, dict):
        return {k: convert_to_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_strings(item) for item in obj]
    else:
        return str(obj)

def get_custom_fields():
    
    url = 'https://api.sky.blackbaud.com/constituent/v1/constituents/customfields?limit=5000'
    params = {}
    
    pagination_api_request(url, params)
    
    # Load to Dataframe
    load_from_json_to_parquet()

def data_pre_processing():
    
    data = pd.read_parquet('Databases/Custom Fields')
    
    # Convert to Datetime format
    data['date_added'] = pd.to_datetime(data['date_added'], utc=True)
    
    data['date'] = data['date_added'].dt.strftime('%d-%m-%Y')
    data['date'] = pd.to_datetime(data['date'], format='%d-%m-%Y', errors='coerce')
    
    # Adding verified sources
    data['verified_source'] = data[['category', 'comment']].apply(lambda x: verified_sources(*x), axis = 1)
    
    # Adding sync sources
    data[['sync_source', 'update_type']] = data[['value']].apply(lambda x: pd.Series(sync_source(x[0])), axis=1)
    
    # Adding Type of Email
    data['comment'].fillna('', inplace=True)
    data['email_type'] = data['comment'].apply(lambda x: email_type(x))
    
    # Extracting domain of email address
    data['email_domain'] = data['comment'].apply(lambda x: extract_domain(x))
    
    # export from dataframe to parquet
    data.to_parquet('Databases/Custom Fields', index=False)

# Function to extract domain from email
def extract_domain(email):
    
    try:
        domain = email.split('@')[1]
    except:
        domain = np.NaN
    
    return domain

def email_type(email):
    
    iitb_emails = ['iitb.ac.in', 'sjmsom.in', 'iitbombay.org']
    
    if any(text in email for text in iitb_emails):
        type = 'IITB Email'
    
    elif '@' in email:
        type = 'Non-IITB Email'
    
    else:
        type = np.NaN
    
    return type

def verified_sources(category, comment):
    
    if 'verified' in str(category).lower():
        
        if comment == 'verified using RE appeal data':
            output = 'RE Email Engagement - Open rate'
        
        else:
            try:
                output = str(comment).split('-')[0].strip().title()
            except:
                output = str(comment).strip().title()
    else:
        output = np.NaN
    
    return output

def sync_source(source):
    
    to_check = ['- manually |', '- manual |', '- auto |', '- automatically |']
    
    if any(string in str(source).lower() for string in to_check):
        try:
            sync_source = str(source).split('-')[0].strip()
        except:
            sync_source = str(source).strip()
        
        try:
            update_type = str(source).split('|')[1].strip().title() 
        except:
            update_type = str(source).strip().title()
    
    else:
        sync_source = np.NaN
        update_type = np.NaN
    
    if 'email' in str(update_type).lower():
        update_type = 'Email'
    elif 'phone' in str(update_type).lower():
        update_type = 'Phone'
    elif update_type == 'Linkedin':
        update_type = 'Online Presence'
    elif 'employment' in str(update_type).lower() or 'org' in str(update_type).lower():
        update_type = 'Employment'
    elif 'address' in str(update_type).lower() or 'location' in str(update_type).lower():
        update_type = 'Location'
    elif 'gender' in str(update_type).lower() or 'name' in str(update_type).lower() or 'pan' in str(update_type).lower() or 'bio' in str(update_type).lower():
        update_type = 'Bio Details'
    
    return sync_source, update_type

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
    
    # Get Custom fields data of all constituent
    get_custom_fields()
    
    # Data Pre-processing
    data_pre_processing()

except Exception as Argument:
    
    logging.error(Argument)
    
    send_error_emails('Error while downloading data from RE for Dashboard | Database Update Form-Model', Argument)

finally:
    
    # Housekeeping
    housekeeping()
    
    # Stop Logging
    stop_logging()
        
    exit()