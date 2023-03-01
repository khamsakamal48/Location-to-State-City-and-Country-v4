import requests
import os
import json
import glob
import smtplib
import ssl
import imaplib
import datetime
import logging
import pandas as pd

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from jinja2 import Environment
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

def send_error_emails(subject):
    logging.info('Sending email for an error')
    
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = MAIL_USERN
    message['To'] = SEND_TO

    # Adding Reply-to header
    message.add_header('reply-to', MAIL_USERN)
        
    TEMPLATE='''
    <table style='background-color: #ffffff; border-color: #ffffff; width: auto; margin-left: auto; margin-right: auto;'>
    <tbody>
    <tr style='height: 127px;'>
    <td style='background-color: #363636; width: 100%; text-align: center; vertical-align: middle; height: 127px;'>&nbsp;
    <h1><span style='color: #ffffff;'>&nbsp;Raiser's Edge Automation: {{job_name}} Failed</span>&nbsp;</h1>
    </td>
    </tr>
    <tr style='height: 18px;'>
    <td style='height: 18px; background-color: #ffffff; border-color: #ffffff;'>&nbsp;</td>
    </tr>
    <tr style='height: 18px;'>
    <td style='width: 100%; height: 18px; background-color: #ffffff; border-color: #ffffff; text-align: center; vertical-align: middle;'>&nbsp;<span style='color: #455362;'>This is to notify you that execution of Auto-updating Alumni records has failed.</span>&nbsp;</td>
    </tr>
    <tr style='height: 18px;'>
    <td style='height: 18px; background-color: #ffffff; border-color: #ffffff;'>&nbsp;</td>
    </tr>
    <tr style='height: 61px;'>
    <td style='width: 100%; background-color: #2f2f2f; height: 61px; text-align: center; vertical-align: middle;'>
    <h2><span style='color: #ffffff;'>Job details:</span></h2>
    </td>
    </tr>
    <tr style='height: 52px;'>
    <td style='height: 52px;'>
    <table style='background-color: #2f2f2f; width: 100%; margin-left: auto; margin-right: auto; height: 42px;'>
    <tbody>
    <tr>
    <td style='width: 50%; text-align: center; vertical-align: middle;'>&nbsp;<span style='color: #ffffff;'>Job :</span>&nbsp;</td>
    <td style='background-color: #ff8e2d; width: 50%; text-align: center; vertical-align: middle;'>&nbsp;{{job_name}}&nbsp;</td>
    </tr>
    <tr>
    <td style='width: 50%; text-align: center; vertical-align: middle;'>&nbsp;<span style='color: #ffffff;'>Failed on :</span>&nbsp;</td>
    <td style='background-color: #ff8e2d; width: 50%; text-align: center; vertical-align: middle;'>&nbsp;{{current_time}}&nbsp;</td>
    </tr>
    </tbody>
    </table>
    </td>
    </tr>
    <tr style='height: 18px;'>
    <td style='height: 18px; background-color: #ffffff;'>&nbsp;</td>
    </tr>
    <tr style='height: 18px;'>
    <td style='height: 18px; width: 100%; background-color: #ffffff; text-align: center; vertical-align: middle;'>Below is the detailed error log,</td>
    </tr>
    <tr style='height: 217.34375px;'>
    <td style='height: 217.34375px; background-color: #f8f9f9; width: 100%; text-align: left; vertical-align: middle;'>{{error_log_message}}</td>
    </tr>
    </tbody>
    </table>
    '''
    
    # Create a text/html message from a rendered template
    emailbody = MIMEText(
        Environment().from_string(TEMPLATE).render(
            job_name = subject,
            current_time=datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            error_log_message = Argument
        ), 'html'
    )
    
    # Add HTML parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(emailbody)
    attach_file_to_email(message, 'Process.log')
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
        imap.append('Sent', '\\Seen', imaplib.Time2Internaldate(datetime.now()), emailcontent.encode('utf8'))
        imap.logout()

def attach_file_to_email(message, filename):
    
    # Open the attachment file for reading in binary mode, and make it a MIMEApplication class
    with open(filename, 'rb') as f:
        file_attachment = MIMEApplication(f.read())
        
    # Add header/name to the attachments    
    file_attachment.add_header(
        'Content-Disposition',
        f'attachment; filename= {filename}',
    )
    
    # Attach the file to the message
    message.attach(file_attachment)

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
    
    # Get a list of all the file paths that ends with wildcard from in specified directory
    fileList = glob.glob('API_Response_RE_*.json')
    
    for each_file in fileList:
        
        # Open Each JSON File
        with open(each_file, 'r') as json_file:
            
            # Load JSON File
            json_content = json.load(json_file)
            
            # Load from JSON to pandas
            reff = pd.json_normalize(json_content['value'])
            
            # Load to a dataframe
            df_ = pd.DataFrame(data=reff)
            
            try:
                # Append/Concat datframes
                df = pd.concat([df, df_])
                
            except:
                df = df_.copy()
                
    # export from dataframe to parquet
    df = df[['address', 'constituent_id']]
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