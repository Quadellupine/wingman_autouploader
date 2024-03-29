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
from batchupload import batch_upload_window
from batchupload import write_log
# Queue for multithreading
result_queue = queue.Queue()
# Load configuration
config = configparser.ConfigParser()
config_file_path = "config.ini"
if not os.path.exists(config_file_path):
    with open("config.ini", 'w') as file:
        # Create .ini file with some defaults
        file.write("[Settings]\nshowwipes = False\nlogpath=.\ntheme = Topanga\npushwipes = False\nno_wingman = False\nfilter_shitlogs = True\nheight=500\nwidth=450")
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
    height = config["Settings"]["height"]
    width = config["Settings"]["width"]
    size_tuple = (width, height)
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
    if domain >= 15:
        print(get_current_time(),"Reached 15 retries. Aborting.")
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
        #print(data)
        dps_link = data['permalink']
    except Exception as e:
        print(get_current_time(),"Error, retrying(",2**domain,"s): ", e)
        time.sleep(2**domain) #exponential backoff
        return dpsreport_fixed(file_to_upload, domain+1, result_queue)
    success_value = data.get('encounter', {}).get('success')
    try:
         test = data['permalink']
    except Exception as e:
        print(get_current_time(),"Error, retrying(",2**domain,"s): ", e)
        time.sleep(2**domain) #exponential backoff
        return dpsreport_fixed(file_to_upload, domain+1)
    print(get_current_time(),"permalink:", data['permalink'])
    duration = get_json_duration(dps_link)
    print(get_current_time(),"Success:",success_value, "| Duration:", duration)
    result_queue.put((success_value, dps_link, duration))
    write_log(file_to_upload)
    return success_value, dps_link, duration

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
# Wow binary tables actually being useful for once
def reprint():
    print("reprinting...")
    window["text"].update("")
    for link in link_collection:
        if link[0] or showwipes:
            if not (is_shitlog(link[1]) and filter_shitlogs):
                window["text"].print("[",link[2],"]",link[1])
# Begin the actual PROGRAM
# ----------------  Create main Layout  ----------------
textbox = [sg.Multiline('', size=(120, 20), key='text', autoscroll=True, disabled=True)]
button_row_one= [sg.Button("Reset", size=(26, 2)),
     sg.Button("Copy last to Clipboard", size=(26, 2))]

button_row_two =[sg.Button("Copy all to Clipboard", size=(26, 2)),
      sg.Button("Copy only Kills", size=(26,2))]
checkbox_one = [sg.Checkbox("Show wipes  ", key='wipes', default=showwipes),
      sg.Checkbox("Upload wipes to Wingman", key ='bool_wingman', default=pushwipes)]
checkbox_two = [sg.Checkbox("Filter shitlogs", key ='shitlog_checkbox', default=filter_shitlogs),
        sg.Checkbox("Disable Wingman Upload", key='global_wingman', default=no_wingman)]
batch_upload = [sg.Button("Batch Upload", key="batch", size=(13,1))]

layout = [textbox, button_row_one, button_row_two, checkbox_one, checkbox_two, batch_upload]
# Set icon on windows, still need to figure out how to detect Linux binaries
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir="."
icon_path = os.path.join(base_dir, 'icon.ico')
window = sg.Window('Autouploader', layout, auto_size_buttons=True, keep_on_top=False, grab_anywhere=True, resizable=True, size=size_tuple, icon="icon.ico")
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
#result_queue.put((True, "_trio", 0))
#result_queue.put((False, "_trio", 0))

try:
    while True:
        time.sleep(0.05)
        event, values = window.read(timeout=100)
        try:
            success_value, dps_link, duration = result_queue.get_nowait()
            bool_shitlog = is_shitlog(dps_link)
            # Filter logs that nobody wants to see anyways...
            if (bool_shitlog and not filter_shitlogs) or (not bool_shitlog):
                if (success_value == True or pushwipes == True) and no_wingman == False:
                    upload_wingman(dps_link)
                else:
                    print(get_current_time(),"Not pushing to wingman")
                link_collection.append((success_value, dps_link, duration))
                if dps_link == "skip":
                    continue
                # Only printing successful logs to GUI or if the user wants wipes

                if success_value or showwipes and (not bool_shitlog):
                    window["text"].print("[",duration,"]",dps_link)
        except queue.Empty:
            pass
        #Check for events, extremely UGLY but what can you do
        if event == sg.WIN_CLOSED or event == 'Exit':
            with open(config_file_path, 'w') as configfile:
                config.write(configfile)
            break
        # Open additional Window to start a batch upload, handled in additional python file
        elif event == "batch":
            batch_upload_window(path)
            
        # Copying last visible link to clipboard
        elif event == "Copy last to Clipboard":
            last = window["text"].get()
            last = last.split("\n")[-1]
            if last != "":
                last = last.split("]")[1]
            pyperclip.copy(last)
        # Copy all visible links to clipboard
        elif event == "Copy all to Clipboard":
            s = ""
            for entry in link_collection:
                if entry[0] or showwipes:
                    if not (is_shitlog(entry[1]) and filter_shitlogs):
                        s = s+(entry[1])+"\n"
            pyperclip.copy(s)
        # Only copy kills, even if wipes are visible
        elif event == "Copy only Kills":
            s = ""
            for entry in link_collection:
                if entry[0] == True and not (is_shitlog(entry[1]) and filter_shitlogs):
                    s = s+(entry[1])+"\n"
            pyperclip.copy(s)
        # Reset memory of links
        elif event == "Reset":
            window["text"].update("")
            link_collection = []  
        # Upload wipes              
        elif values['wipes'] == True:
            config.set('Settings', 'ShowWipes', 'True')
            if values["wipes"] != showwipes:
                showwipes = True
                reprint()          
        elif values['wipes'] == False:
            config.set('Settings', 'ShowWipes', 'False')
            if values["wipes"] != showwipes:
                showwipes = False
                reprint()
        # Push to wingman
        if values['bool_wingman'] == True:
            config.set('Settings', 'pushwipes', 'True')
            pushwipes = True
        elif values['bool_wingman'] == False:
            config.set('Settings', 'pushwipes', 'False')
            pushwipes = False
        # Disable wingmanupload entirely
        if values['global_wingman'] == True:
            config.set('Settings', 'no_wingman', 'True')
            no_wingman = True
        elif values['global_wingman'] == False:
            config.set('Settings', 'no_wingman', 'False')
            no_wingman = False
        # Filter Shitlogs
        if values['shitlog_checkbox'] == True:
            config.set('Settings', 'filter_shitlogs', 'True')
            if values['shitlog_checkbox'] != filter_shitlogs:
                filter_shitlogs = True 
                reprint()               
        elif values['shitlog_checkbox'] == False:
            config.set('Settings', 'filter_shitlogs', 'False')
            if values['shitlog_checkbox'] != filter_shitlogs:
                filter_shitlogs = False
                reprint()
            
except KeyboardInterrupt:
    my_observer.stop()
    my_observer.join()
except Exception as e:
    print("Oh no!")
    exception = str(e)
    now = datetime.now()
    filename = now.strftime("%d_%m_%Y_%H:%M:%S")
    filename = filename+"_crash.txt"
    f = open(filename, "w+")
    f.write(exception)
    f.close()