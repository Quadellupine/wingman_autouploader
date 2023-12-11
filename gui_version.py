import time
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import sys
import os
import requests
import PySimpleGUI as sg
import pyperclip
import configparser
import queue
# Queue for multithreading
result_queue = queue.Queue()

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
    showwipes = config.getboolean('Settings', 'showwipes')
    path = config["Settings"]["logpath"]
    sg.theme(config["Settings"]["theme"])
    pushwipes = config.getboolean('Settings', 'pushwipes')
    no_wingman = config.getboolean('Settings', 'no_wingman')
    filter_shitlogs = config.getboolean('Settings', 'filter_shitlogs')
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
            time.sleep(5)
        print(get_current_time(), event.dest_path.split(path)[1],"log creation has now finished")
        window.start_thread(lambda: dpsreport_fixed(event.dest_path, 0, result_queue), ('-THREAD-', '-THEAD ENDED-'))

def get_current_time():
    ts = time.time()
    date_time = datetime.fromtimestamp(ts)
    ts = date_time.strftime("%H:%M:%S")
    ts = "["+ts+"]:"
    return ts

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


def upload_wingman(dps_link):
    url = "https://gw2wingman.nevermindcreations.de/api/importLogQueued"
    params = {"link": dps_link, 'antibot': 'true'}
    response = requests.get(url, params=params)
    data = response.json()
    print(get_current_time(),data['note'])


def dpsreport_fixed(file_to_upload, domain, result_queue):
    if domain >= 20:
        print(get_current_time(),"Reached 100 retries. Aborting.")
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
        print(get_current_time(),"Error, retrying(",2**domain,"s): ", e)
        time.sleep(2**domain) #exponential backoff
        return dpsreport_fixed(file_to_upload, domain+1, result_queue)
    success_value = data.get('encounter', {}).get('success')
    print(get_current_time(),"permalink:", data['permalink'])
    print(get_current_time(),"Success:",success_value, "| Duration:", get_json_duration(dps_link))
    result_queue.put((success_value, dps_link))
    return success_value, dps_link

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

# ----------------  Create Form  ----------------
layout = [
    [sg.Multiline('', size=(120, 20), key='text', autoscroll=True, disabled=True)],
    [sg.Button("Exit", size=(26, 2)),
     sg.Button("Copy last to Clipboard", size=(26, 2))],
     [sg.Button("Copy all to Clipboard", size=(26, 2)),
      sg.Button("Copy only Kills", size=(26,2))],
     [sg.Checkbox("Show wipes", key='wipes', default=showwipes),
      sg.Checkbox("Upload wipes to Wingman", key ='bool_wingman', default=pushwipes)],
      [sg.Checkbox("Filter shitlogs", key ='shitlog_checkbox', default=filter_shitlogs),
        sg.Checkbox("Disable Wingman Upload", key='global_wingman', default=no_wingman)]
]
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir="."
icon_path = os.path.join(base_dir, 'icon.ico')
window = sg.Window('Autouploader', layout, auto_size_buttons=True, keep_on_top=False, grab_anywhere=True, resizable=True, size=(450,470), icon="icon.ico")
window.set_icon(icon_path)
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



try:
    while True:
        time.sleep(0.05)
        event, values = window.read(timeout=100)
        try:
            success_value, dps_link= result_queue.get_nowait()
            bool_shitlog = is_shitlog(dps_link)
            # Filter logs that nobody wants to see anyways...
            if (bool_shitlog and not filter_shitlogs) or (not bool_shitlog):
                if (success_value == True or pushwipes == True) and no_wingman == False:
                    upload_wingman(dps_link)
                else:
                    print(get_current_time(),"Not pushing to wingman")
                link_collection.append((success_value, dps_link))
                if dps_link == "skip":
                    continue
                # --------- Append to text content --------
                # Only printing successful logs to GUI or if the user wants wipes

                if success_value or showwipes:
                    window['text'].print("[",get_json_duration(dps_link),"]",dps_link)
        except queue.Empty:
            pass
        # -- Check for events --B
        if event == sg.WIN_CLOSED or event == 'Exit':
            with open(config_file_path, 'w') as configfile:
                config.write(configfile)
            break
            
        elif event == "Copy last to Clipboard":
            if link_collection:
                pyperclip.copy(link_collection[-1][1])
        elif event == "Copy all to Clipboard":
            s = ""
            for entry in link_collection:
                s = s+(entry[1])+"\n"
            pyperclip.copy(s)
        elif event == "Copy only Kills":
            s = ""
            for entry in link_collection:
                if entry[0] == True:
                    s = s+(entry[1])+"\n"
            pyperclip.copy(s)
                    
        elif values['wipes'] == True:
            config.set('Settings', 'ShowWipes', 'True')
            showwipes = True
        elif values['wipes'] == False:
            config.set('Settings', 'ShowWipes', 'False')
            showwipes = False
        if values['bool_wingman'] == True:
            config.set('Settings', 'pushwipes', 'True')
            pushwipes = True
        elif values['bool_wingman'] == False:
            config.set('Settings', 'pushwipes', 'False')
            pushwipes = False
        if values['global_wingman'] == True:
            config.set('Settings', 'no_wingman', 'True')
            no_wingman = True
        elif values['global_wingman'] == False:
            config.set('Settings', 'no_wingman', 'False')
            no_wingman = False
        if values['shitlog_checkbox'] == True:
            config.set('Settings', 'filter_shitlogs', 'True')
            filter_shitlogs = True
        elif values['shitlog_checkbox'] == False:
            config.set('Settings', 'filter_shitlogs', 'False')
            filter_shitlogs = False
            
except KeyboardInterrupt:
    my_observer.stop()
    my_observer.join()
