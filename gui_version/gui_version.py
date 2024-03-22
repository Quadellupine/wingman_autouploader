import time
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import sys
import requests
import os
import PySimpleGUI as sg
import pyperclip
import configparser
import queue
from batchupload import batch_upload_window
from utils import write_log, get_current_time, start_mono_app, get_info_from_json, get_wingman_percentile, get_path
import wget
import zipfile

# Find latest EI release
EIQueryURL = "https://api.github.com/repos/baaron4/GW2-Elite-Insights-Parser/releases/latest"
# Queue for multithreading
result_queue = queue.Queue()
# Load configuration
config = configparser.ConfigParser()
config_file_path = "config.ini"
data = []
if not os.path.exists(config_file_path):
    with open("config.ini", 'w') as file:
        # Create .ini file with some defaults
        file.write("[Settings]\nshowwipes = False\nlogpath=.\ntheme = Topanga\npushwipes = False\nno_wingman = False\nfilter_shitlogs = True\nheight=500\nwidth=470")
        file.close()
    config.read(config_file_path)
        
# Apply retrieved config
try:
    config.read(config_file_path)
    showwipes = config.getboolean('Settings', 'showwipes')
    path = config["Settings"]["logpath"]
    logpath = config["Settings"]["logpath"]
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
        window.start_thread(lambda: upload(event.dest_path,no_wingman), ('-THREAD-', '-THEAD ENDED-'))

      
def upload(log,wingman):
    linux = ["-p"]
    if not wingman:
        configpath = get_path()+"wingman.conf"
        config = ["-c", configpath]
    else:
        configpath = get_path()+"no_wingman.conf"
        config = ["-c", configpath]
    print(get_current_time(),"Selected config: ",config)
    args = linux + config + [log]
    start_mono_app("EI/GuildWars2EliteInsights.exe",args)
    ei_log = log.replace(".zevtc", ".log")
    with open(ei_log) as f:
        lines = f.readlines()
    os.remove(ei_log) 
    dps_link=""
    for line in lines:        
        if "dps.report" in line:
            dps_link=line.split(" ")[1]
            dps_link = dps_link.replace("\n","")
            print(get_current_time(),"permalink:",dps_link)
        if "Wingman: UploadProcessed" in line:
            print(get_current_time(),line.replace("\n",""))
    duration, success_value = get_info_from_json(dps_link)
    result_queue.put((success_value, dps_link, duration))
    write_log(log)
    

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

# Clear table
def clear_table():
    global data 
    data = []
    window["table"].update(values=data)
# Wow binary tables actually being useful for once
def reprint():
    print(get_current_time(),"Reprint requested, trying to fetch percentiles again...")
    clear_table()
    for link in link_collection:
        if link[0] or showwipes:
            if not (is_shitlog(link[1]) and filter_shitlogs):
                percentile = get_wingman_percentile(link[1])
                if percentile == None:
                    percentile = "..."
                new_entry = [
                link[2],
                link[1],
                link[0]
                ]
                data.append(new_entry)
                # Update the table
                window["table"].update(values=data)
                
# Check for EI
if not os.path.isdir("EI"):
    print(get_current_time(),"EI is missing, downloading it")
    query = requests.get(EIQueryURL).json()
    print("Version: ",query["tag_name"])
    recentEI = query["assets"][0]
    assetURL = recentEI["browser_download_url"]
    wget.download(assetURL, "EI.zip")
    with zipfile.ZipFile("EI.zip", 'r') as zip_ref:
        zip_ref.extractall("EI")
    os.remove("EI.zip")
    
# Begin the actual PROGRAM
# ----------------  Create main Layout  ----------------
headings = ['Time', 'Link', 'Wipe']
col_widths = [5, 32, 7]
textbox = [
    sg.Table(
        values=[],headings=headings,
        key='table',
        expand_x=True,
        expand_y=True,
        enable_click_events=True,
        auto_size_columns=False,
        col_widths=col_widths, 
        row_height=20, 
        justification="center",
        header_relief="RELIEF_FLAT")]
button_row_one= [sg.Button("Reset", size=(26, 2)),
     sg.Button("Copy last to Clipboard", size=(26, 2))]

button_row_two =[sg.Button("Copy all to Clipboard", size=(26, 2)),
      sg.Button("Copy only Kills", size=(26,2))]
checkbox_one = [sg.Checkbox("Show wipes  ", key='wipes', default=showwipes),
                sg.Checkbox("Filter shitlogs", key ='shitlog_checkbox', default=filter_shitlogs)]
checkbox_two = [sg.Checkbox("Disable Wingman Upload", key='global_wingman', default=no_wingman)]
batch_upload = [sg.Button("Batch Upload", key="batch", size=(13,1)), 
                sg.Button("Refresh(debug)", key="refresh", size=(13,1))]
seperator = [sg.HorizontalSeparator()]

layout = [textbox, button_row_one, button_row_two, checkbox_one, checkbox_two,seperator, batch_upload]
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
result_queue.put((True, "https://dps.report/NxAB-20240320-215554_matt", 0))
result_queue.put((False, "_trio_wipe", 0))
#upload("/mnt/Storage/Logs/arcdps.cbtlogs/Standard Kitty Golem/20240221-182436.zevtc",False)
try:
    while True:
        time.sleep(0.05)
        event, values = window.read(timeout=100)
        # The threads will place finished logs in a queue. The GUI periodically checks for new logs in the queue and then processes them
        try:
            success_value, dps_link, duration = result_queue.get_nowait()
            link_collection.append((success_value, dps_link, duration))
            # Print according to user selection
            reprint()
        except queue.Empty:
            pass
        
        #Check for events, extremely UGLY but what can you do
        if event == sg.WIN_CLOSED or event == 'Exit':
            with open(config_file_path, 'w') as configfile:
                config.write(configfile)
            break
        # Open additional Window to start a batch upload, handled in additional python file
        elif event == "refresh":
            reprint()
        elif event == "batch":
            batch_upload_window(logpath)
        elif '+CLICKED+' in event:
            # The event objects contains: The source, the event name and then the cell that has been clicked as a tuple. This means we can access the row like this:
            row = event[2][0]
            try:        
                # Now we look up the log in the data array, which holds the contents of the table that is displayed
                selected_link = data[row][1]
                pyperclip.copy(selected_link)
                sg.popup_notify('Copied!',display_duration_in_ms = 700, fade_in_duration=0)
            except:
                pass
        # Copying last visible link to clipboard
        elif event == "Copy last to Clipboard":
            try:
                last = window["table"].get()
                last = last[-1][1]
            except:
                last = ""
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
            clear_table()
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
    print(e)
    exception = str(e)
    now = datetime.now()
    filename = now.strftime("%d_%m_%Y_%H:%M:%S")
    filename = filename+"_crash.txt"
    f = open(filename, "w+")
    f.write(exception)
    f.close()