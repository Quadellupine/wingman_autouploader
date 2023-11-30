import os
import time
import requests
from datetime import datetime
import PySimpleGUI as sg
import pyperclip
from tkinter import ttk


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
    json_data = response.json()
    success_value = json_data.get('encounter', {}).get('success')

    if response.status_code != 200:
        print(get_current_time(),"An error has occured while uploadng to dps.report, aborting...")
        print(get_current_time(),"Errorcode:",response.status_code)
        if response.status_code == 403:
            print(get_current_time(),"Most likely ratelimited: Retrying in 30 seconds.")
            time.sleep(30)
            # this could be a recursive hellscape
            upload_dpsreport(file_to_upload)
        return False

    data = response.json()
    print(get_current_time(),"permalink:", data['permalink'])
    dps_link = data['permalink']
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
polling_interval = 2

initial_run = True

# ----------------  Create Form  ----------------
sg.theme("Dark Teal 10")
sg.set_options(element_padding=(0, 0))
default_color = sg.theme_background_color()
button_color_options = (default_color,default_color)
workingdir = os.getcwd()

layout = [
    [sg.Text("Watching "+workingdir+" for new logs\n", justification='center')],
    [sg.Multiline('', size=(80, 40), key='text', autoscroll=True, disabled=True)],
         [sg.Button("Exit",pad=((10, 10), (10, 10)),size=(15,2)),
          sg.Button("Copy last to Clipboard",pad=((10, 10), (10, 10)),size=(20,2)),
          sg.Button("Copy all to Clipboard",pad=((10, 10), (10, 10)),size=(20,2))
          ]]

window = sg.Window('Autouploader', layout, no_titlebar=False, auto_size_buttons=False, keep_on_top=False, grab_anywhere=True)



# ----------------  Main Loop  ----------------
text_content = ""
dps_link_old = ""
dps_link = ""
while True:
    # --------- Read and update window --------
    event, values = window.read(timeout=1000)
    # --- Do evtc logic
    for root, _, files in os.walk(path):
        for file in files:
            #print(file)
            if file.endswith(".zevtc"):
                file_path = os.path.join(root, file)
                file_mtime = os.path.getmtime(file_path)
                if file_path not in seen_files and file_mtime != start_time:
                    print(get_current_time(),"New file detected:",file)
                    # Make sure to not somehow upload the same file twice
                    seen_files.add(file_path)
                    # Upload to dps.report
                    success_value, dps_link = upload_dpsreport(file_path)
                    print(get_current_time(),"Success:",success_value)
                    # Only upload to wingman if it wasnt a wipe/check whether it was
                    if success_value:
                        upload_wingman(dps_link)
                    else:
                        print(get_current_time(),"Not pushing wipes to wingman")
    
            # --------- Append to text content --------
            if dps_link != dps_link_old:
                text_content += dps_link+ "\n"
                window['text'].update(value=text_content)
                dps_link_old = dps_link
            
            
    # -- Check for events --
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    elif event == "Copy last to Clipboard":
        pyperclip.copy(dps_link)
    elif event == "Copy all to Clipboard":
        pyperclip.copy(text_content)

    #time.sleep(polling_interval)