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
else:
    with open("config.ini", 'w') as file:
    # Write content to the file
        file.write("[Settings]\nshowwipes = False")
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
            time.sleep(30)
            # this could be a recursive hellscape
            upload_dpsreport(file_to_upload)
        return False, "skip"

    data = response.json()
    print(get_current_time(),"permalink:", data['permalink'])
    dps_link = data['permalink']
    success_value = data.get('encounter', {}).get('success')
    return success_value, dps_link

def check_success(url):
    r = requests.get(url)
    r.encoding = 'utf-8'
    response = r.text
    if " Result: Success " in response: 
        print(get_current_time(),"Log is a kill")
        return True
    else:
        print(get_current_time(),"Log is a wipe")
        return False

seen_files = set()

path = "."

initial_run = True

# ----------------  Create Form  ----------------
sg.theme("Dark Teal 10")

workingdir = os.getcwd()

layout = [
    [sg.Multiline('', size=(120, 20), key='text', autoscroll=True, disabled=True)],
    [sg.Button("Exit", size=(26, 2)),
     sg.Button("Copy last to Clipboard", size=(26, 2))],
     [sg.Button("Copy all to Clipboard", size=(26, 2)),
     sg.Button("Copy all to Clipboard incl Wipes", size=(26, 2))],
     [sg.Checkbox("Show wipes", key='s1', default=checkbox_default)]
]

window = sg.Window('Autouploader', layout, no_titlebar=False, auto_size_buttons=True, keep_on_top=False, grab_anywhere=True, resizable=True, size=(450,450))



# ----------------  Main Loop  ----------------
text_content = ""
dps_link_old = ""
dps_link = ""
all_links=[]
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
                    # Make sure to not somehow upload the same file twice (failsafe, dont know if necessary)
                    seen_files.add(file_path)
                    # Upload to dps.report
                    success_value, dps_link = upload_dpsreport(file_path)
                    if dps_link == "skip":
                        continue
                    all_links.append(dps_link+"\n")
                    print(get_current_time(),"Success:",success_value)
                    # --------- Append to text content --------
                    if dps_link != dps_link_old:
                        # Only printing successful logs to GUI
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
        config['Settings'] = {'ShowWipes': str(values['s1'])}
        with open(config_file_path, 'w') as configfile:
            config.write(configfile)
        break
    elif event == "Copy last to Clipboard":
        lines = text_content.split('\n')
        pyperclip.copy(lines[-2])
        print(lines)
    elif event == "Copy all to Clipboard":
        lines = text_content.split('\n')
        s = ''.join(lines)
        pyperclip.copy(s)
    elif event == "Copy all to Clipboard incl Wipes":
        s = "".join(all_links)
        pyperclip.copy(s)