import time
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os
import requests
import PySimpleGUI as sg
import pyperclip
import configparser
import queue


# Load configuration
config = configparser.ConfigParser()
config_file_path = "config.ini"
if not os.path.exists(config_file_path):
    with open("config.ini", 'w') as file:
        # Create .ini file with some defaults
        file.write("[Settings]\nshowwipes = False\nlogpath=.\ntheme = Dark Teal 12")
        file.close()
    config.read(config_file_path)
        
# Apply retrieved config
try:
    config.read(config_file_path)
    checkbox_default = config.getboolean('Settings', 'showwipes')
    path = config["Settings"]["logpath"]
    sg.theme(config["Settings"]["theme"])
except:
    sg.popup("Malformed config.ini. Delete it to generate a clean one.",title="Error")
    exit()


# Watchdog Eventhandling
def on_created(event):
    return

def on_deleted(event):
    return

def on_modified(event):
    return

def on_moved(event):
    historicalSize = -1
    if event.dest_path not in seen_files and (event.dest_path.endswith(".zevtc")):
        seen_files.append(event.dest_path)
        while (historicalSize != os.path.getsize(event.dest_path)):
            historicalSize = os.path.getsize(event.dest_path)
            time.sleep(1)
        print(get_current_time(), event.dest_path.split(path)[1]," log creation has now finished")
        upload_dpsreport(event.dest_path, 1)

def get_current_time():
    ts = time.time()
    date_time = datetime.fromtimestamp(ts)
    ts = date_time.strftime("%H:%M:%S")
    ts = "["+ts+"]:"
    return ts


def upload_wingman(dps_link):
    url = "https://gw2wingman.nevermindcreations.de/api/importLogQueued"
    params = {"link": dps_link, 'antibot': 'true'}
    response = requests.get(url, params=params)
    data = response.json()
    print(get_current_time(),data['note'])


def upload_dpsreport(file_to_upload, domain):
    if domain == 1:
        url = "https://dps.report/uploadContent"
    elif domain == 2:
        url = "https://b.dps.report/uploadContent"
    elif domain == 3:
        url = "http://a.dps.report/uploadContent"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',}   
    files = {'file': (file_to_upload, open(file_to_upload, 'rb'))}
    data = {'json': '1', 'generator': 'ei'}

    response = requests.post(url, files=files, data=data, headers=headers)

    if response.status_code != 200:        
        success_value = False
        dps_link = "skip"
        print(get_current_time(),"An error has occured while uploadng to dps.report")
        print(get_current_time(),"Errorcode:",response.status_code)
        if domain==1:
            print(get_current_time(),"Trying b.dps.report")
            time.sleep(3)
            success_value,dps_link = upload_dpsreport(file_to_upload, 2)
        elif domain ==2:
            time.sleep(3)
            print(get_current_time(), "Trying a.dps.report")
            success_value,dps_link = upload_dpsreport(file_to_upload, 3)
        return success_value, dps_link

    data = response.json()
    dps_link = data['permalink']
    success_value = data.get('encounter', {}).get('success')
    print(get_current_time(),"permalink:", data['permalink'])
    print(get_current_time(),"Success:",success_value)
    if success_value == True:
            upload_wingman(dps_link)
    else:
        print(get_current_time(),"Not pushing wipes to wingman")
    return success_value, dps_link




patterns = ["*"]
ignore_patterns = None
ignore_directories = False
case_sensitive = True
my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)

my_event_handler.on_created = on_created
my_event_handler.on_deleted = on_deleted
my_event_handler.on_modified = on_modified
my_event_handler.on_moved = on_moved

go_recursively = True
my_observer = Observer()
my_observer.schedule(my_event_handler, path, recursive=go_recursively)
my_observer.start()

start_time = time.time()
# Keeping track of the seen files is necessary because somehow the modified event gets procced a million times
seen_files = []
link_collection = []

print("Watching Logfolder:",path)
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    my_observer.stop()
    my_observer.join()
