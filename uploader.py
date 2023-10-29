# Watchdog tutorial I used as basis: https://thepythoncorner.com/posts/2019-01-13-how-to-create-a-watchdog-in-python-to-look-for-filesystem-changes/
# curl to post directly from bash if its all you need: curl -F 'file=@test.zevtc' "https://dps.report/uploadContent?json=1&genertor=ei"  
import requests
import time
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from datetime import datetime

# ADD YOUR PATH HERE
path = "."


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
            sleep(60)
            # this could be a recursive hellscape
            upload_dpsreport(file_to_upload)
        return False

    data = response.json()
    print(get_current_time(),"permalink:", data['permalink'])
    dps_link = data['permalink']
    return dps_link

def get_current_time():
    ts = time.time()
    date_time = datetime.fromtimestamp(ts)
    ts = date_time.strftime("%H:%M:%S")
    ts = "["+ts+"]"
    return ts

def on_created(event):
    
    print(get_current_time(),f"{event.src_path} has been created.")
    if event.src_path[-6:] != ".zevtc":
        print(get_current_time(),"Ignoring because this is not an arcdps log.")
        return
    # Upload the given log to dps.report    
    dps_link = upload_dpsreport(event.src_path)
    if not dps_link:
        print(get_current_time(),"Nothing to pass to wingman. Skipping.")
    else:
        upload_wingman(dps_link)
    print(get_current_time(),"Done handling log.")

def on_deleted(event):
    print(get_current_time(),f"Deleted {event.src_path}.")


# I thought it would make sense to write a log but I also realized its kind of pointless lmao. Then i ended up doing printf debugging 
# and have somehwat of a log anyways now. sigh.
eventhandler = LoggingEventHandler()
eventhandler.on_created = on_created
eventhandler.on_deleted = on_deleted

go_recursively = True
observer = Observer()
observer.schedule(eventhandler, path, recursive=go_recursively)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    observer.join()

