import requests
import os
import json
import glob
import datetime
import logging
import msal
import pandas as pd
import numpy as np
import base64

from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from dotenv import load_dotenv

def set_current_directory():

    logging.info('Setting current directory')
    
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
    
    global RE_API_KEY, O_CLIENT_ID, CLIENT_SECRET, TENANT_ID, FROM, CC_TO, ERROR_EMAILS_TO, SEND_TO

    load_dotenv()

    RE_API_KEY = os.getenv('RE_API_KEY')
    O_CLIENT_ID = os.getenv('O_CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TENANT_ID = os.getenv('TENANT_ID')
    FROM = os.getenv('FROM')
    SEND_TO = eval(os.getenv('SEND_TO'))
    CC_TO = eval(os.getenv('CC_TO'))
    ERROR_EMAILS_TO = eval(os.getenv('ERROR_EMAILS_TO'))

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
                    'Attachments': [
                        {
                            '@odata.type': '#microsoft.graph.fileAttachment',
                            'name': 'Process.log',
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

    global email_providers
    
    # Get a list of all the file paths that ends with wildcard from in specified directory
    fileList = glob.glob('API_Response_RE_*.json')

    df = pd.DataFrame()

    for each_file in fileList:
        
        # Open Each JSON File
        with open(each_file, 'r') as json_file:
            
            # Load JSON File
            json_content = json.load(json_file)
            
            # Load from JSON to pandas
            reff = pd.json_normalize(json_content['value'])
            
            # Load to a dataframe
            df_ = pd.DataFrame(data=reff)

            # Append/Concat dataframes
            df = pd.concat([df, df_])

    email_providers = pd.read_csv('Databases/Email Providers.csv')
    email_providers = email_providers['email_providers'].drop_duplicates().tolist()
                
    # export from dataframe to parquet
    df = df[['address', 'constituent_id', 'id', 'primary', 'type']].copy()

    df[['domain', 'domain_category']] = df[['address', 'address']].apply(lambda x: get_domain(*x), result_type='expand', axis=1)

    df.to_parquet('Databases/System Record IDs', index=False)

def get_request_re(url, params):
    
    global re_api_response
    
    logging.info('Running GET Request from RE function')
    
    # Request Headers for Blackbaud API request
    headers = {
    # Request headers
    'Bb-Api-Subscription-Key': RE_API_KEY,
    'Authorization': 'Bearer ' + access_token,
    }
    
    re_api_response = http.get(url, params=params, headers=headers).json()

def get_domain(email, email1):

    if '@' in email:
        domain = email.split('@')[1].lower()

        if domain == 'gmail.com': return domain, '1 - Gmail'
        elif domain == 'iitbombay.org': return domain, '4 - IITBOMBAY.ORG'
        elif domain in email_providers: return domain, '2 - Others'
        else: return domain, '3 - Business'

    else: return np.NaN, np.NaN

try:
    
    # Start Logging for Debugging
    start_logging()
    
    # Set current directory
    set_current_directory()
    
    # Retrieve contents from .env file
    get_env_variables()
    
    # Housekeeping
    housekeeping()
    
    # Set API Request strategy
    set_api_request_strategy()
    
    # Retrieve access_token from file
    retrieve_token()
    
    # Get List of Alums with Email
    url = 'https://api.sky.blackbaud.com/constituent/v1/emailaddresses?limit=5000'
    params = {}
    pagination_api_request(url=url, params=params)
    
    # Load from JSON
    load_from_json_to_parquet()
    
except Exception as Argument:
    
    logging.error(Argument)
    
    send_error_emails('Error while downloading Emails | Location to State, City and Country v4')

finally:
    
    # Housekeeping
    housekeeping()
    
    # Stop Logging
    stop_logging()
        
    exit()