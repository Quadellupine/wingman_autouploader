import os
import time
import requests
from datetime import datetime
import PySimpleGUI as sg
import pyperclip
import configparser
import queue
# Queue for multithreading and global variables
result_queue = queue.Queue()
path = "."
checkbox_default = False
sg.theme("Dark Brown 3")

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

def get_current_time():
    ts = time.time()
    date_time = datetime.fromtimestamp(ts)
    ts = date_time.strftime("%H:%M:%S")
    ts = "["+ts+"]:"
    return ts


def upload_wingman(dps_link):
    url = "https://gw2wingman.nevermindcreations.de/api/importLogQueued"
    params = {"link": dps_link}
    response = requests.get(url, params=params)
    data = response.json()
    print(get_current_time(),data['note'])


def upload_dpsreport(file_to_upload, domain, result_queue):
    if domain == 1:
        url = "https://dps.report/uploadContent"
    elif domain == 2:
        url = "https://b.dps.report/uploadContent"
    elif domain == 3:
        url = "http://a.dps.report/uploadContent"
    files = {'file': (file_to_upload, open(file_to_upload, 'rb'))}
    data = {'json': '1', 'generator': 'ei'}

    response = requests.post(url, files=files, data=data)

    if response.status_code != 200:        
        success_value = False
        dps_link = "skip"
        print(get_current_time(),"An error has occured while uploadng to dps.report")
        print(get_current_time(),"Errorcode:",response.status_code)
        if domain==1:
            print(get_current_time(),"Trying b.dps.report")
            time.sleep(3)
            success_value,dps_link = upload_dpsreport(file_to_upload, 2, result_queue)
        elif domain ==2:
            time.sleep(3)
            print(get_current_time(), "Trying a.dps.report")
            success_value,dps_link = upload_dpsreport(file_to_upload, 3, result_queue)
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
    result_queue.put((success_value, dps_link))
    return success_value, dps_link



# ----------------  Create Form  ----------------
layout = [
    [sg.Multiline('', size=(120, 20), key='text', autoscroll=True, disabled=True)],
    [sg.Button("Exit", size=(26, 2)),
     sg.Button("Copy last to Clipboard", size=(26, 2))],
     [sg.Button("Copy all to Clipboard", size=(26, 2)),
      sg.Button("Copy only Kills", size=(26,2))],
     [sg.Checkbox("Show wipes", key='s1', default=checkbox_default)]
]

window = sg.Window('Autouploader', layout, no_titlebar=False, auto_size_buttons=True, keep_on_top=False, grab_anywhere=True, resizable=True, size=(450,470),icon='icon.png')



# ----------------  Main Loop  ----------------
start_time = time.time()
text_content = ""
seen_files = set()
link_collection = []
# Main program Loop, Logic happens here
while True:
    # --------- Read and update window --------
    event, values = window.read(timeout=100)
    # Find all files
    for root, _, files in os.walk(path):
        for file in files:
            # Find all files with zevtc extension
            if file.endswith(".zevtc"):
                file_path = os.path.join(root, file)
                file_mtime = os.path.getmtime(file_path)
                # Select only files that we havent seen before and that are created after starttime of the program
                if file_path not in seen_files and file_mtime > start_time:
                    print(get_current_time(),"New file detected:",file)
                    seen_files.add(file_path)
                    # Start a new thread to upload files
                    window.start_thread(lambda: upload_dpsreport(file_path, 1, result_queue), ('-THREAD-', '-THEAD ENDED-'))

            
    # Check queue for new logs to handle
    try:
        success_value, dps_link = result_queue.get_nowait()
        link_collection.append((success_value, dps_link))
        if dps_link == "skip":
            continue
        # --------- Append to text content --------
        # Only printing successful logs to GUI or if the user wants wipes
        checkbox_status = values['s1']
        if success_value or checkbox_status:
            text_content += dps_link+ "\n"
            window['text'].update(value=text_content)
    except queue.Empty:
        pass  
    
    
    # -- Check for events --
    if event == sg.WIN_CLOSED or event == 'Exit':
        with open(config_file_path, 'w') as configfile:
            config.write(configfile)
        break
        
    elif event == "Copy last to Clipboard":
        lines = text_content.split('\n')
        if len(lines) > 1:
            pyperclip.copy(lines[-2])
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
                
    elif values['s1'] == True:
        config.set('Settings', 'ShowWipes', 'True')
    elif values['s1'] == False:
        config.set('Settings', 'ShowWipes', 'False')
        
        
        
window.close()