import os
import time
import requests
from datetime import datetime
import PySimpleGUI as sg
import pyperclip
import configparser

# Load configuration
config = configparser.ConfigParser()
config_file_path = "config.ini"

if os.path.exists(config_file_path):
    config.read(config_file_path)
    checkbox_default = config.getboolean('Settings', 'ShowWipes')
    path = config["Settings"]["logpath"]
else:
    with open("config.ini", 'w') as file:
    # Write content to the file
        file.write("[Settings]\nshowwipes = False\nlogpath=.")
        path="."
    checkbox_default = False
start_time = time.time()
seen_files = set()

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
        if domain=="a":
            print(get_current_time(),"Trying b.dps.report")
            time.sleep(3)
            success_value,dps_link = upload_dpsreport(file_to_upload, "b")
        elif domain =="b":
            time.sleep(3)
            print(get_current_time(), "Trying a.dps.report")
            success_value,dps_link = upload_dpsreport(file_to_upload, "c")
        return success_value, dps_link

    data = response.json()
    print(get_current_time(),"permalink:", data['permalink'])
    dps_link = data['permalink']
    success_value = data.get('encounter', {}).get('success')
    return success_value, dps_link



# ----------------  Create Form  ----------------
sg.theme("Dark Black")

workingdir = os.getcwd()

layout = [
    [sg.Multiline('', size=(120, 20), key='text', autoscroll=True, disabled=True)],
    [sg.Button("Exit", size=(26, 2)),
     sg.Button("Copy last to Clipboard", size=(26, 2))],
     [sg.Button("Copy all to Clipboard", size=(26, 2)),
     sg.Button("Copy all to Clipboard incl Wipes", size=(26, 2))],
     [sg.Checkbox("Show wipes", key='s1', default=checkbox_default)]
]

window = sg.Window('Autouploader', layout, no_titlebar=False, auto_size_buttons=True, keep_on_top=False, grab_anywhere=True, resizable=True, size=(450,470),icon='icon.png')



# ----------------  Main Loop  ----------------
text_content = ""
dps_link_old = ""
dps_link = ""
all_links=[]
lines=[]
while True:
    # --------- Read and update window --------
    event, values = window.read(timeout=10)
    # --- Do evtc logic
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
                    success_value, dps_link = upload_dpsreport(file_path,"a")
                    if dps_link == "skip":
                        continue
                    all_links.append(dps_link+"\n")
                    print(get_current_time(),"Success:",success_value)
                    # --------- Append to text content --------
                    if dps_link != dps_link_old:
                        # Only printing successful logs to GUI or if the user wants wipes
                        checkbox_status = values['s1']
                        if success_value or checkbox_status:
                            text_content += dps_link+ "\n"
                            window['text'].update(value=text_content)
                        dps_link_old = dps_link
                    # Only uploading successful logs to wingman
                    if success_value:
                        upload_wingman(dps_link)
                    else:
                        print(get_current_time(),"Not pushing wipes to wingman")

            
            
    # -- Check for events --
    if event == sg.WIN_CLOSED or event == 'Exit':
        config.set('Settings', 'ShowWipes', str(values['s1']))
        with open(config_file_path, 'w') as configfile:
            config.write(configfile)
        break
        
    elif event == "Copy last to Clipboard":
        lines = text_content.split('\n')
        if len(lines) > 1:
            pyperclip.copy(lines[-2])
    elif event == "Copy all to Clipboard":
        lines = text_content.split('\n')
        s = "\n".join(lines)
        if len(lines)>1:
            pyperclip.copy(s)
    elif event == "Copy all to Clipboard incl Wipes":
        s = "\n".join(all_links)
        pyperclip.copy(s)
        
        
window.close()