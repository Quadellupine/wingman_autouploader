import time 
from datetime import datetime
import subprocess
import os
import requests
import numpy as np
import platform

def write_log(text):
    try:
        with open(".seen.csv", "a") as f:
            f.write(str(text)+"\n")
    except:
        f = open(".seen.csv", "x")
        f.close
        write_log(text)

def get_current_time():
    ts = time.time()
    date_time = datetime.fromtimestamp(ts)
    ts = date_time.strftime("%H:%M:%S")
    ts = "["+ts+"]:"
    return ts
def start_mono_app(app_path, app_arguments):
    osname = platform.system()
    if osname =="Windows":
        subprocess.run([app_path] + app_arguments)
    else:
        try:
            # Use subprocess to start the Mono app with arguments
            subprocess.run(['mono', app_path] + app_arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"Error starting Mono app: {e}")
        except FileNotFoundError:
            print("Mono runtime not found. Make sure Mono is installed on your system.")     
def get_info_from_json(dps_link):
    try:
        url = "https://dps.report/getJson?permalink="+dps_link
        response = requests.get(url)
        content = response.json()
        duration = content.get("duration")
        success = content.get("success")
        parts = duration.split()
        duration = parts[0]+parts[1]
    except Exception as e:
        print(e)
        duration = "0"
        success = False
    return duration, success

def return_json(dps_link):
    url = "https://dps.report/getJson?permalink="+dps_link
    response = requests.get(url)
    content = response.json()
    return content


def get_wingman_percentile(log):
    # Get only postfix of log with dps.report shebang in the front
    postfix = log.split("/")[-1]
    url = "https://gw2wingman.nevermindcreations.de/api/getPercentileOfLog/"+postfix
    response = requests.get(url)
    content = response.json()
    return content.get("percentile")

def get_path():
    path = os.path.abspath(__file__)
    path = path.rstrip(os.path.basename(__file__))
    return path
