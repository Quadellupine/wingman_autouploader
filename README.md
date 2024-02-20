# Scuffed little uploader
Threw it together because the official uploader doesn't work on Linux. Or maybe I'm just stupid.
Does nothing fancy, it watches for new logs and uploads them to dps.report and then adds that to the wingman queue.
```uploader.py``` is the CLI Version that I personally use. ```gui_version.py``` obviously is the GUI Version for the LESS STRONG MINDED people. 

# Disclaimer: Use at your own risk
I am trying my best, but I can't take responsibility for this app crashing or not working correctly. If you find any mistakes please let me know.
# Windows
1. Download the latest .exe from the "Release" page
2. Stop your antivirus from blocking it
3. It will create a config.ini file, put your log path into it
# Linux
Currently I am not providing a binary for Linux. 
1. Install python, then install the dpendencies ```pysimplegui, pyperclip, requests, watchdog``` using
pip
2. Run the script using ```python3 gui_version.py``` or ```python3  uploader.py```
3. It will create a config.ini file. Edit it to include your logpath
# Some tips
1. I usually place this window on a seperate workspace. On windows, you can access this feature using
```Ẁindows + Tab```.
2. You can choose your own theme. Check https://media.geeksforgeeks.org/wp-content/uploads/20200511200254/f19.jpg for the available themes.
3. Please report any issues you have on this repo, and suggestions too. I will try to work on them but
I cant promise anything.
4. If you want to see detailed output you should run the terminal version of the app. It will tell you if/when uploads fail, which will make debugging much easier. If the app crashes it will provide a crashdump txt file, please include it if you want to report a crash.
# Batch Upload
Clicking the button opens a second window. While it is open progress on the main window will be held back
until it is closed. This is due to my incompetence and may be fixable.
In the new window, you can choose a folder. When you click upload the program will recursively go down the
folder you have given it (So including subfolders) and upload anything it finds.<br>
After your first time using this feature, a file called .seen.csv will be created. It will keep track of all
successfully uploaded files to prevent them from being reuploaded again in the future.
**ATTENTION**
If you CLOSE to batchupload window the uploading will continue in the background. Only clicking the CANCEL button or fully terminating the Application will stop it.
# Etc
Feel free to steal this for anything. Maybe I'll make it less scuffed in the future.<br>
Last tested with my python 3.7 setup on Arch Linux and the state of dps.report/wingman APIs as of 27.10.2023.
# Licenses of used packages
requests: Apache 2.0 <br>
psyimplegui: GNU LESSER GENERAL PUBLIC LICENSE<br>
pyperclip: See licenses.txt<br>
watchdog: Apache 2.0
