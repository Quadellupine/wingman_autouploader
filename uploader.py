# ADD YOUR PATH HERE
path = "."

# Watchdog tutorial I used as basis: https://thepythoncorner.com/posts/2019-01-13-how-to-create-a-watchdog-in-python-to-look-for-filesystem-changes/
# curl to post directly from bash if its all you need: curl -F 'file=@test.zevtc' "https://dps.report/uploadContent?json=1&genertor=ei"  
import requests
import time
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
import json

def upload_wingman(dps_link):
    url = "https://gw2wingman.nevermindcreations.de/api/importLogQueued"
    params = {"link": dps_link}
    response = requests.get(url, params=params)
    data = response.json()
    print(data['note'])


def upload_dpsreport(file_to_upload):
    url = "https://dps.report/uploadContent"
    files = {'file': (file_to_upload, open(file_to_upload, 'rb'))}
    data = {'json': '1', 'generator': 'ei'}

    response = requests.post(url, files=files, data=data)

    if response.status_code != 200:
        print("An error has occured while uploadng to dps.report, aborting...")
        print("Errorcode:"response.status_code)
        return "nothing"
    # Success!!
    data = response.json()
    print("permalink:", data['permalink'])
    dps_link = data['permalink']
    return dps_link

def on_created(event):
    print(f"{event.src_path} has been created.")
    # Upload the given log to dps-report    
    dps_link = upload_dpsreport(event.src_path)
    if dps_link == "nothing":
        "Nothing to pass to wingman. Skipping."
    else:
        upload_wingman(dps_link)
    print("Done handling log.")

def on_deleted(event):
    print(f"Deleted {event.src_path}.")


# I thought it would make sense to write a log but I also realized its kind of pointless lmao
eventhandler = LoggingEventHandler()
eventhandler.on_created = on_created
eventhandler.on_deleted = on_deleted

# ADD YOUR PATH HERE
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

