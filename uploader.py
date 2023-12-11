import time
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os
import requests
import PySimpleGUI as sg
import configparser
with open('ascii.txt', 'r') as f:
    print(f.read())

# Load configuration
config = configparser.ConfigParser()
config_file_path = "config.ini"
if not os.path.exists(config_file_path):
    with open("config.ini", 'w') as file:
        # Create .ini file with some defaults
        file.write("[Settings]\nshowwipes = False\nlogpath=.\ntheme = Dark Teal 12\npushwipes = False\nno_wingman = False")
        file.close()
    config.read(config_file_path)
        
# Apply retrieved config
try:
    config.read(config_file_path)
    checkbox_default = config.getboolean('Settings', 'showwipes')
    path = config["Settings"]["logpath"]
    sg.theme(config["Settings"]["theme"])
    pushwipes = config["Settings"]["pushwipes"]
    no_wingman = config.getboolean('Settings', 'no_wingman')
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
    domain = domain % 3
    if domain == 0:
        url = "https://dps.report/uploadContent"
    elif domain == 1:
        url = "https://b.dps.report/uploadContent"
    elif domain == 2:
        url = "http://a.dps.report/uploadContent" 
    files = {'file': (file_to_upload, open(file_to_upload, 'rb'))}
    data = {'json': '1', 'generator': 'ei'}
    headers = {'Accept': 'application/json'}
    try:
        response = requests.post(url, files=files, data=data, timeout=30, headers=headers)
    except Exception as e:
        print(get_current_time(),"Error, retrying(",2**domain,"s): ", e)
        time.sleep(2**domain) #exponential backoff
        return upload_dpsreport(file_to_upload, domain+1)
    data = response.json()
    dps_link = data['permalink']
    success_value = data.get('encounter', {}).get('success')
    print(get_current_time(),"permalink:", data['permalink'])
    print(get_current_time(),"Success:",success_value)
    return success_value, dps_link





patterns = ["*"]
ignore_patterns = None
ignore_directories = False
case_sensitive = True
event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)

event_handler.on_created = on_created
event_handler.on_deleted = on_deleted
event_handler.on_modified = on_modified
event_handler.on_moved = on_moved

go_recursively = True
my_observer = Observer()
my_observer.schedule(event_handler, path, recursive=go_recursively)
my_observer.start()

# Keeping track of the seen files is necessary because somehow the modified event gets procced a million times
seen_files = []

print("Watching Logfolder:",path)
try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    my_observer.stop()
    my_observer.join()
