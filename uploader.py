import os
import time
import requests
from datetime import datetime
import json

start_time = time.time()
seen_files = set()

def get_current_time():
    ts = time.time()
    date_time = datetime.fromtimestamp(ts)
    ts = date_time.strftime("%H:%M:%S")
    ts = "["+ts+"]"
    return ts


def upload_wingman(dps_link):
    url = "https://gw2wingman.nevermindcreations.de/api/importLogQueued"
    params = {"link": dps_link}
    response = requests.get(url, params=params)
    data = response.json()
    print(get_current_time(),data['note'])


def upload_dpsreport(file_to_upload, domain):
    if domain == "a":
        url = "https://dps.report/uploadContent"
    elif domain == "b":
        url = "https://b.dps.report/uploadContent"
    elif domain == "c":
        url = "http://a.dps.report/uploadContent"
    files = {'file': (file_to_upload, open(file_to_upload, 'rb'))}
    data = {'json': '1', 'generator': 'ei'}

    response = requests.post(url, files=files, data=data)

    if response.status_code != 200:        
        success_value = False
        dps_link = "skip"
        print(get_current_time(),"An error has occured while uploadng to dps.report")
        print(get_current_time(),"Errorcode:",response.status_code)
        if response.status_code == 403 and domain=="a":
            print(get_current_time(),"Trying b.dps.report")
            success_value,dps_link = upload_dpsreport(file_to_upload, "b")
        elif response.status_code == 403 and domain =="b":
            print(get_current_time(), "Trying a.dps.report")
            success_value,dps_link = upload_dpsreport(file_to_upload, "c")
        return success_value, dps_link

    data = response.json()
    print(get_current_time(),"permalink:", data['permalink'])
    dps_link = data['permalink']
    success_value = data.get('encounter', {}).get('success')
    return success_value, dps_link


seen_files = set()

path = "."
polling_interval = 2

initial_run = True

while True:
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".zevtc"):
                file_path = os.path.join(root, file)
                file_mtime = os.path.getmtime(file_path)
                if file_path not in seen_files and file_mtime > start_time:
                    print(get_current_time(),"New file detected:",file)
                    seen_files.add(file_path)
                    success_value, dps_link = upload_dpsreport(file_path, "a") 
                    if success_value:
                        upload_wingman(dps_link)

    time.sleep(polling_interval)