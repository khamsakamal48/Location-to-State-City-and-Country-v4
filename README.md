# Data updates from MS Form to Raisers Edge & Reporting

## Install Pre-requisites
```bash
sudo apt install -y systemd

# Python Packages
pip install requests
pip install streamlit
pip install python-dotenv
pip install regex
pip install pandas
pip install fuzzywuzzy
pip install python-Levenshtein
pip install nameparser
pip install plotly-express
pip install openpyxl
pip install chardet
pip install tensorflow
pip install scikit-learn
pip install msal
```

## How to run streamlit as service and reverse proxy through NGINX
https://medium.com/@teshanuka/a-simple-guide-to-setup-your-python-code-as-a-systemd-service-7ddba2074039
https://medium.com/codex/setup-a-python-script-as-a-service-through-systemctl-systemd-f0cc55a42267
https://ngbala6.medium.com/deploy-streamlit-app-on-nginx-cfa327106050

### Create a new service with below parameters
```shell
[Unit]
Description=Data Helper service
After=multi-user.target
[Service]
user={{user}}
Type=simple
Restart=always
WorkingDirectory=/{{path}}/Location-to-State-City-and-Country-v4/
ExecStart=/{{conda_path}}/anaconda3/bin/conda run --name {{conda_instance_name}} /{{conda_path}}/anaconda3/bin/streamlit run "/{{path}}/Location-to-State-City-and-Country-v4/Data Helper.py"
[Install]
WantedBy=multi-user.target
```