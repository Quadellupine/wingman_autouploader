import PySimpleGUI as sg
import os
import math
from os import walk, path
import time
from datetime import datetime
import threading
import csv

# Create a Semaphore to control the number of threads
exit_event = threading.Event()
counter_lock = threading.Lock()
counter = 0
global_length = 1
max_threads = 3
thread_semaphore = threading.Semaphore(max_threads)
import subprocess

def execute_dps_report_batch_with_semaphore(log, wingman):
    with thread_semaphore:
        if not exit_event.is_set():
            upload([log], wingman)
            
def start_mono_app(app_path, app_arguments):
    try:
        # Use subprocess to start the Mono app with arguments
        subprocess.run(['mono', app_path] + app_arguments, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting Mono app: {e}")
    except FileNotFoundError:
        print("Mono runtime not found. Make sure Mono is installed on your system.")

def intersection(logs, seen):
    set_logs = set(logs)
    set_seen = set(seen)
    result = list(set_logs - set_seen)
    return result

def get_current_time():
    ts = time.time()
    date_time = datetime.fromtimestamp(ts)
    ts = date_time.strftime("%H:%M:%S")
    thread_name = threading.current_thread().name
    thread_name = thread_name.split(" ")[0]
    thread_name = thread_name.strip("'")
    ts = "["+ts+"]"+thread_name+":"
    return ts
        
def batch_upload_window(path):
    layout = [[sg.Text("Choose a folder for batch upload", key="second",font=('Helvetica', 16))],
              [[sg.FolderBrowse(key="folder",size=(10,1),initial_folder=path), sg.Text(""),]],
              [sg.Button("Upload!", key="upload",size=(10,1)),
               sg.ProgressBar(max_value=100, orientation='h', size=(20, 20), key='progress')],
              [sg.Button("Cancel", key="Exit",size=(10,1)),sg.Text("Status:"),sg.Text("Waiting for Input", key="status")]]
    global counter
    global global_length
    window = sg.Window("Batch Upload", layout, modal=False,enable_close_attempted_event=True)
    while True:
        time.sleep(0.1)
        event, values = window.read(timeout=100)
        window.write_event_value("refresh", counter) 
        if event == "Close" or event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
            print(get_current_time(),"Closing Dialog...")
            break      
        if event == "refresh":
            try:
                progress = math.ceil(counter/len(logs)*100)
                if counter == len(logs):
                    window["status"].update("Done!")                   
            except:
                progress = 0
            window["progress"].update(progress)
        if event == "folder":
            target = values["folder"]
        if event == "Exit":
            print(get_current_time(),"Canceling...")
            try:
                global_length = len(logs)
            except:
                global_length = 1
            window["status"].update("Upload stopping...")  
            exit_event.set()
        if event == "upload":     
            # Reset counter, if user uploads twice in one session, unblock threads
            counter = 0
            exit_event.clear()
            target = values["folder"]
            filenames = []
            for root, _, files in walk(target):
                for filename in files:
                    filenames.append(str(root)+"/"+str(filename))
            # Throw out every file that is not an evtc file
            logs = []
            for file in filenames:
                if file[-4:] == "evtc":
                    logs.append(file)
            seen = return_seen()
            logs = intersection(logs, seen)
            # Set progress bar max to the amount of logs found, reset bar to 0
            window["progress"].update(0)
            window.refresh()   
            print(get_current_time(),"Batchupload: found", len(logs), "new logs")
            window["status"].update("Uploading "+str(len(logs))+" logs")
            window.refresh()
            if len(logs) == 0:
                time.sleep(3)
                window["status"].update("Done!")
                window.refresh()
            for log in logs:
                threading.Thread(target=execute_dps_report_batch_with_semaphore, args=(log, False)).start()  
    window.close()
def write_log(text):
    try:
        with open(".seen.csv", "a") as f:
            f.write(str(text)+"\n")
    except:
        f = open(".seen.csv", "x")
        f.close
        write_log(text)
def return_seen():
    seen = []
    try:
        with open('.seen.csv', newline='') as csvfile:
            seen = list(csv.reader(csvfile))
    except:
        f = open(".seen.csv", "x")
        f.close
    seen = [element for sublist in seen for element in sublist]
    return seen
        
def upload(log,wingman):
    global counter
    linux = ["-p"]
    if wingman:
        config = ["-c", "gui_version/wingman.conf"]
    else:
        config = ["-c", "gui_version/no_wingman.conf"]
    args = linux + config + log
    print("[DEBUG] Arglist:", args)
    start_mono_app("EI/GuildWars2EliteInsights.exe",args)
    time.sleep(15)
    ei_log = log[0].replace(".zevtc", ".log")
    with open(ei_log) as f:
        lines = f.readlines()
    os.remove(ei_log) 
    for  line in lines:
        if "dps.report" in line:
            dps_link=line.split(" ")[1]
            print(dps_link)
            write_log(log[0])
            with counter_lock:
                counter += 1
            