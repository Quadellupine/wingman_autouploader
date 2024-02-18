import PySimpleGUI as sg
import requests
import os
from os import walk
import time
from datetime import datetime
import threading

# Create a Semaphore to control the number of threads
max_threads = 3
thread_semaphore = threading.Semaphore(max_threads)

def execute_dps_report_batch_with_semaphore(log, param):
    with thread_semaphore:
        dps_report_batch(log, param)

def get_current_time():
    ts = time.time()
    date_time = datetime.fromtimestamp(ts)
    ts = date_time.strftime("%H:%M:%S")
    thread_name = threading.current_thread().name
    thread_name = thread_name.split(" ")[0]
    thread_name = thread_name.strip("'")
    ts = "["+ts+"]"+thread_name+":"
    return ts

def upload_wingman_batch(dps_link):
    url = "https://gw2wingman.nevermindcreations.de/api/importLogQueued"
    params = {"link": dps_link, 'antibot': 'true'}
    response = requests.get(url, params=params)
    data = response.json()
    print(get_current_time(),"Batchupload:", data['note'])
        
def batch_upload_window():
    layout = [[sg.Text("Choose a folder for batch upload", key="second")],
              [[sg.FolderBrowse(key="folder"), sg.Text("Progress")]],
              [sg.Button("Upload!", key="upload"),
               sg.ProgressBar(max_value=5, orientation='h', size=(20, 20), key='progress')]]
    window = sg.Window("Second Window", layout, modal=True)
    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "folder":
            path = values["folder"]
        if event == "upload":            
            path = values["folder"]
            filenames = next(walk(path), (None, None, []))[2]
            logs = []
            # Throw out every log that is not an evtc file
            for file in filenames:
                if file[-4:] == "evtc":
                    logs.append(path+"/"+file)
            # Set progress bar max to the amount of logs found
            window['progress'].update(max=len(logs))
            window['progress'].update(current_count = 0)
            # Necessary for update to actually apply...
            event, values = window.read()
            for log in logs:
                threading.Thread(target=execute_dps_report_batch_with_semaphore, args=(log, 0)).start()
            window['progress'].update(current_count = len(logs))
            
                
        
    window.close()
    
    
def dps_report_batch(file_to_upload, domain):
    if domain >= 15:
        return("Failed")
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
    except Exception as e:
        print(get_current_time(),"Error, retrying(",2**domain,"s): ", e)
        time.sleep(2**domain) #exponential backoff
        return dps_report_batch(file_to_upload, domain+1)
    print(get_current_time(),"Batchupload:", data['permalink'])
    upload_wingman_batch(data['permalink'])
    return data['permalink']
