import os
import time
import requests
from datetime import datetime
import PySimpleGUI as sg

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
            time.sleep(30)
            # this could be a recursive hellscape
            upload_dpsreport(file_to_upload)
        return False

    data = response.json()
    print(get_current_time(),"permalink:", data['permalink'])
    dps_link = data['permalink']
    return dps_link


seen_files = set()

path = "."
polling_interval = 2

initial_run = True

# ----------------  Create Form  ----------------
sg.theme('Dark Blue')
sg.set_options(element_padding=(0, 0))

layout = [[sg.Multiline('', size=(40, 20), key='text', autoscroll=True)],
         [sg.Button('Exit')]]

# --- systray
menu_def = ['BLANK', ['&Open', '&Save', '---', '&Exit']]

system_tray = sg.SystemTray(menu=menu_def, filename=r'icon.png', tooltip='Autouploader')
window = sg.Window('Autouploader', layout, no_titlebar=False, auto_size_buttons=False, keep_on_top=False, grab_anywhere=True)



# ----------------  Main Loop  ----------------
text_content = "Welcome!\n"
counter = 0
dps_link=""
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
    
    # --------- Read and update window --------
    event, values = window.read(timeout=10)
    
    # --------- Append to text content --------
    if dps_link:
        text_content = dps_link+ "\n"
    
    # --------- Update Multiline element --------
    window['text'].update(value=text_content)
    
    # -- Check for events --
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    counter = counter+1

    time.sleep(polling_interval)