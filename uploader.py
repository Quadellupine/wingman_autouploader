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
        file.write("[Settings]\nshowwipes = False\nlogpath=.\ntheme = Dark Teal 12\npushwipes = False\nno_wingman = False\nfilter_shitlogs = True")
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
        dps_link, success_value = upload_dpsreport(event.dest_path, 1)
        if (success_value == True or pushwipes == True) and no_wingman == False:
                    upload_wingman(dps_link)
        else:
            print(get_current_time(),"Not pushing to wingman")
        print("-----------------------------------------------------------------------------------")


def get_current_time():
    ts = time.time()
    date_time = datetime.fromtimestamp(ts)
    ts = date_time.strftime("%H:%M:%S")
    ts = "["+ts+"]:"
    return ts

def is_shitlog(dps_link):
    shitlogs =[
    "_trio",
    "_tc",
    "_esc",
    "_bk",
    "_eyes",
    "_se",
    "_rr"
    ]
    for substring in shitlogs:
        if substring in dps_link:
            return True
    return False

def upload_wingman(dps_link):
    url = "https://gw2wingman.nevermindcreations.de/api/importLogQueued"
    params = {"link": dps_link, 'antibot': 'true'}
    response = requests.get(url, params=params)
    data = response.json()
    print(get_current_time(),data['note'])

def get_json_duration(dps_link):
    try:
        url = "https://dps.report/getJson?permalink="+dps_link
        response = requests.get(url)
        content = response.json()
        duration = content.get("duration")
        parts = duration.split()
        duration = parts[0]+parts[1]
    except:
        duration = "0"
    return duration

def upload_dpsreport(file_to_upload, domain):
    if domain >= 20:
        print(get_current_time(),"Reached 20 retries. Aborting.")
        return(False, "skip")
    if domain % 3 == 0:
        url = "https://dps.report/uploadContent"
    elif domain % 3 == 1:
        url = "https://b.dps.report/uploadContent"
    elif domain % 3 == 2:
        url = "http://a.dps.report/uploadContent" 
    files = {'file': (file_to_upload, open(file_to_upload, 'rb'))}
    data = {'json': '1', 'generator': 'ei'}
    headers = {'Accept': 'application/json'}
    try:
        response = requests.post(url, files=files, data=data, timeout=30, headers=headers)
        # Make the response is actually there?? idk at this point
        time.sleep(6)
        data = response.json()
        dps_link = data['permalink']
    except Exception as e:
        print(get_current_time(),"Error, retrying(",2*domain,"s): ", e)
        time.sleep(2*domain) #exponential backoff
        return upload_dpsreport(file_to_upload, domain+1)
    success_value = data.get('encounter', {}).get('success')
    print(get_current_time(),"permalink:", dps_link)
    print(get_current_time(),"Success:",success_value, "| Duration:", get_json_duration(dps_link))
    return dps_link, success_value





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
