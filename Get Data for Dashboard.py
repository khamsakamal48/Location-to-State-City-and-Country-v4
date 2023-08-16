import requests
import os
import json
import glob
import datetime
import logging
import base64
import msal
import pandas as pd
import numpy as np

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
    
    global RE_API_KEY, O_CLIENT_ID, CLIENT_SECRET, TENANT_ID, FROM, CC_TO, ERROR_EMAILS_TO, SEND_TO, LIST_1

    load_dotenv()

    RE_API_KEY = os.getenv('RE_API_KEY')
    O_CLIENT_ID = os.getenv('O_CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TENANT_ID = os.getenv('TENANT_ID')
    FROM = os.getenv('FROM')
    SEND_TO = eval(os.getenv('SEND_TO'))
    CC_TO = eval(os.getenv('CC_TO'))
    ERROR_EMAILS_TO = eval(os.getenv('ERROR_EMAILS_TO'))
    LIST_1 = os.getenv('LIST_1') # Opt outs list

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

def send_error_emails(subject, Argument):
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
            
        with open(f'API_Response_RE_{process_name}_{i}.json', 'w', encoding='utf-8') as list_output:
            json.dump(re_api_response, list_output, ensure_ascii=True, sort_keys=True, indent=4)
        
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
        with open(each_file, 'r', encoding='utf8') as json_file:
            
            # Load JSON File
            json_content = json.load(json_file)
            
            # Convert non-string values to strings
            json_content = convert_to_strings(json_content)
            
            # Load to a dataframe
            df_ = api_to_df(json_content)
            
            df = pd.concat([df, df_])
    
    return df

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

    categories = ['Verified Email', 'Verified Phone', 'Sync source', 'Verified Location']

    df = pd.DataFrame()

    for category in categories:
        url = f'https://api.sky.blackbaud.com/constituent/v1/constituents/customfields?limit=5000&category={category}'
        params = {}
    
        pagination_api_request(url, params)
    
        # Load to Dataframe
        df_1 = load_from_json_to_parquet().copy()
        df = pd.concat([df, df_1])

        # Housekeeping
        housekeeping()
    
    # export from dataframe to parquet
    logging.info('Loading DataFrame to file')
    df.to_parquet('Databases/Custom Fields', index=False)

def data_pre_processing():

    global email_providers
    
    data = pd.read_parquet('Databases/Custom Fields')

    # Convert to Datetime format
    data['date'] = data['date_added'].apply(lambda x: str(x).split('-')[2][0:2] + '-' + str(x).split('-')[1] + '-' + str(x).split('-')[0])
    data['date'] = pd.to_datetime(data['date'], format='%d-%m-%Y', errors='coerce')
    
    # Adding verified sources
    data['verified_source'] = data[['category', 'comment']].apply(lambda x: verified_sources(*x), axis=1)
    
    # Adding sync sources
    data[['sync_source', 'update_type']] = data[['value']].apply(lambda x: pd.Series(sync_source(x[0])), axis=1)
    
    # Check if the value for Update Type = Email is infact an email
    data['update_type'] = data[['update_type', 'comment']].apply(lambda x: check_if_email(*x), axis=1)
    
    # Adding Type of Email
    data['value'] = data['value'].fillna('')
    data['email_type'] = data['value'].apply(lambda x: email_type(x))
    
    # Extracting domain of email address
    data['email_domain'] = data['value'].apply(lambda x: extract_domain(x))
    
    # Checking if new record is an Alum
    data['update_type'] = data[['update_type', 'comment']].apply(lambda x: identify_new_record(*x), axis=1)
    
    # Get city, state and country from the Address List
    data['parent_id'] = data['parent_id'].astype(int)
    
    address_data = pd.read_parquet('Databases/Address List')
    address_data['constituent_id'] = address_data['constituent_id'].astype(int)
    
    data = pd.merge(left=data, right=address_data[['constituent_id', 'city', 'county', 'country']].drop_duplicates(), left_on='parent_id', right_on='constituent_id', how='left')
    data = data.drop(columns=['constituent_id']).copy()

    data['verified_source_category'] = data['verified_source'].apply(lambda x: get_verified_category(x))

    # Source: https://gist.githubusercontent.com/ammarshah/f5c2624d767f91a7cbdc4e54db8dd0bf/raw/660fd949eba09c0b86574d9d3aa0f2137161fc7c/all_email_provider_domains.txt
    email_providers = pd.read_csv('Databases/Email Providers.csv')
    email_providers = email_providers['email_providers'].tolist()
    data['email_domain_category'] = data['email_domain'].apply(lambda x: set_domain_priority(x))
    
    # export from dataframe to parquet
    data.to_parquet('Databases/Custom Fields', index=False)

def set_domain_priority(domain):
    if domain == 'gmail.com': return '1 - Gmail'
    if domain == 'iitbombay.org': return '4 - IITBOMBAY.ORG'
    if domain in email_providers: return '2 - Others'
    if pd.isnull(domain): return np.NaN
    else: return '3 - Business'

# Function to get the category of the verified sources
def get_verified_category(source):
    if source == 'RE Email Engagement_Appeals' or source == 'RE Email Engagement' or source == 'Netcore Email Engagement': return '2 - Opens'
    elif source == 'Live Alumni': return '3 - Live Alumni'
    elif source == 'Alumni Association': return '4 - Alumni Association'
    elif pd.isnull(source) or source == '': return np.NaN
    else: return '1 - Alum'

# Function to extract domain from email
def extract_domain(email):

    if '@' in email: return str(email.split('@')[1]).lower().strip()
    else: return np.NaN

def email_type(email):
    
    if '@' in email and not 'https://' in email:
    
        iitb_emails = ['iitb.ac.in', 'sjmsom.in', 'iitbombay.org']
        
        if any(text in email for text in iitb_emails):
            type = 'IITB Email'
        
        elif '@' in email:
            type = 'Non-IITB Email'
        
        else:
            type = np.NaN
    
    else:
        type = np.NaN
    
    return type

def verified_sources(category, comment):
    
    if 'verified' in str(category).lower():
        
        if comment == 'verified using RE appeal data':
            output = 'RE Email Engagement - Open rate'
        
        try:
            output = str(comment).split('-')[0].strip()
        except:
            output = str(comment).strip()
            
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

def check_if_email(type, email):

    if email is None: return np.NaN
    else:
        if type == 'Email':

            if 'https://' in email:
                type = np.NaN

            else:
                if '@' in email:
                    type = type

                else:
                    type = np.NaN

        return type

def identify_new_record(update_type, type):
    
    if update_type == 'New Record':
        
        if 'alum' in str(type).lower():
            update_type = 'New Alums'
        
        else:
            update_type = update_type
        
    else:
        update_type = update_type
        
    return update_type

def get_addresses():
    
    url = 'https://api.sky.blackbaud.com/constituent/v1/addresses?limit=5000'
    params = {}
    
    pagination_api_request(url, params)
    
    # Load to Dataframe
    df = load_from_json_to_parquet().copy()
    
    # Sort by preferred address
    df = df[df['preferred'] == True].copy()
    
    # export from dataframe to parquet
    logging.info('Loading Address DataFrame to file')
    df.to_parquet('Databases/Address List', index=False)

def get_only_alums():
    logging.info('Getting list of only Alums')

    url = 'https://api.sky.blackbaud.com/constituent/v1/constituents?constituent_code=Alumni&include_inactive=true&include_deceased=true&fields=id,deceased,inactive&limit=5000'
    params = {}

    pagination_api_request(url, params)

    # Load to Dataframe
    df = load_from_json_to_parquet().copy()

    # export from dataframe to parquet
    df.to_parquet('Databases/All Alums.parquet', index=False)

def get_opt_outs():
    logging.info('Getting list of opt-outs')

    url = f'https://api.sky.blackbaud.com/constituent/v1/constituents?list_id={LIST_1}&limit=5000'
    params = {}

    pagination_api_request(url, params)

    # Load to Dataframe
    df = load_from_json_to_parquet().copy()

    # export from dataframe to parquet
    df.to_parquet('Databases/Opt-outs.parquet', index=False)

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

    # Housekeeping
    housekeeping()

    # Get Address data of all constituent
    get_addresses()

    # Data Pre-processing
    data_pre_processing()

    # Get list of Alum
    get_only_alums()

    # Get Opt-outs
    get_opt_outs()

except Exception as Argument:
    
    logging.error(Argument)
    
    send_error_emails('Error while downloading data from RE for Dashboard | Database Update Form-Model', Argument)

finally:
    
    # Housekeeping
    housekeeping()
    
    # Stop Logging
    stop_logging()
        
    exit()