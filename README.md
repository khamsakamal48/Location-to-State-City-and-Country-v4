# Location-to-State-City-and-Country-v4

pip3 install requests
pip3 install streamlit
pip3 install python-dotenv
pip3 install regex
pip3 install pandas
pip3 install fuzzywuzzy
pip3 install python-Levenshtein
pip3 install nameparser
pip3 install plotly-express
pip3 install openpyxl

https://medium.com/@teshanuka/a-simple-guide-to-setup-your-python-code-as-a-systemd-service-7ddba2074039
https://medium.com/codex/setup-a-python-script-as-a-service-through-systemctl-systemd-f0cc55a42267
https://ngbala6.medium.com/deploy-streamlit-app-on-nginx-cfa327106050
pip list -v
sudo apt-get install -y systemd

[Unit]
Description=Data Helper service
After=multi-user.target
[Service]
user=kamal
Type=simple
Restart=always
WorkingDirectory=/home/kamal/Documents/Location-to-State-City-and-Country-v4/
ExecStart=/home/kamal/anaconda3/bin/conda run --name Local /home/kamal/anaconda3/bin/streamlit run "/home/kamal/Documents/Location-to-State-City-and-Country-v4/Data Helper.py"
[Install]
WantedBy=multi-user.target
~                               