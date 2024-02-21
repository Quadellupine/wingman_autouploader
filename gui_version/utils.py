import time 
from datetime import datetime
import subprocess
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
    try:
        # Use subprocess to start the Mono app with arguments
        subprocess.run(['mono', app_path] + app_arguments, check=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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