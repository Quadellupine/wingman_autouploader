import PySimpleGUI as sg
import requests
import math
from os import walk, path
import time
from datetime import datetime
import threading


# Create a Semaphore to control the number of threads
counter = 0
counter_lock = threading.Lock()
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
              [[sg.FolderBrowse(key="folder"), sg.Text("")]],
              [sg.Button("Upload!", key="upload"),
               sg.ProgressBar(max_value=100, orientation='h', size=(20, 20), key='progress')]]
    global counter
    window = sg.Window("Batch Upload", layout, modal=False,enable_close_attempted_event=True)
    while True:
        event, values = window.read(timeout=100)
        window.write_event_value("refresh", counter) 
        if event == "Close" or event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
            print("Closing Dialog...")
            break      
        if event == "refresh":
            try:
                progress = math.ceil(counter/len(logs)*100)                    
            except:
                progress = 0
            window["progress"].update(progress)
        if event == "folder":
            target = values["folder"]
        if event == "upload":     
            # Reset counter, if user uploads twice in one session
            counter = 0
            target = values["folder"]
            filenames = [path.join(root, filename) for root, _, files in walk(target) for filename in files]
            # Throw out every file that is not an evtc file
            logs = []
            for file in filenames:
                if file[-4:] == "evtc":
                    logs.append(file)
            # Set progress bar max to the amount of logs found, reset bar to 0
            window["progress"].update(0)
            window.refresh()   
            print(get_current_time(),"Batchupload: found", len(logs), "logs")
            for log in logs:
                threading.Thread(target=execute_dps_report_batch_with_semaphore, args=(log, 0)).start()  
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
        time.sleep(1)
        data = response.json()
    except Exception as e:
        print(get_current_time(),"Error, retrying(",2**domain,"s): ", e)
        time.sleep(2**domain) #exponential backoff
        return dps_report_batch(file_to_upload, domain+1)
    print(get_current_time(),"Batchupload:", data['permalink'])
    upload_wingman_batch(data['permalink'])
    global counter
    with counter_lock:
        counter += 1
    return data['permalink']
