import os
import time
import requests
from datetime import datetime

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


def upload_dpsreport(file_to_upload):
    url = "https://dps.report/uploadContent"
    files = {'file': (file_to_upload, open(file_to_upload, 'rb'))}
    data = {'json': '1', 'generator': 'ei'}

    response = requests.post(url, files=files, data=data)

    if response.status_code != 200:
        print(get_current_time(),"An error has occured while uploadng to dps.report, aborting...")
        print(get_current_time(),"Errorcode:",response.status_code)
        if response.status_code == 403:
            print(get_current_time(),"Most likely ratelimited: Retrying in 30 seconds.")
            sleep(30)
            # this could be a recursive hellscape
            upload_dpsreport(file_to_upload)
        return False

    data = response.json()
    print(get_current_time(),"permalink:", data['permalink'])
    dps_link = data['permalink']
    return dps_link


seen_files = set()

path = "/run/media/anni/fc6b50db-900a-4258-a804-2770b5997a13/SteamLibrary/steamapps/compatdata/1284210/pfx/drive_c/users/steamuser/Documents/Guild Wars 2/addons/arcdps/arcdps.cbtlogs/"
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
                    dps_link = upload_dpsreport(file_path) 
                    upload_wingman(dps_link)

    time.sleep(polling_interval)