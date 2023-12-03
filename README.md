# Scuffed little uploader
Threw it together because the official uploader doesn't work on Linux. Or maybe I'm just stupid.
Does nothing fancy, it watches for new logs and uploads them to dps.report and then adds that to the wingman queue.
```uploader.py``` is the CLI Version that I personally use. ```gui_version.py``` obviously is the GUI Version for the LESS STRONG MINDED people. 

# CLI Version
 ```pip install requests```
# GUI Version
This shit now has a GUI Version. Its bad and ugly, please improve it if you can. I've never made a GUI before and I still don't really want to. The GUI is multithreaded and there may be concurrency issues. I haven't found any but there may be. Packages required:<br>
```pip install requests pysimplegui pyperclip configparser```<br>
## config.ini
On first run the GUI Program will create a config.ini. You can specify a logpath in there if you want to. Ideally the path should have no spaces. The program checks all subfolders, so you can just specify your path to ```arcdps.cbtlogs```.<br>
It is also possible to choose your own Theme by setting it in the generated .ini file. You can view all avilable themes here:<br>
https://media.geeksforgeeks.org/wp-content/uploads/20200511200254/f19.jpg<br>
Example: ```theme=Dark Brown 3```
# How to use this on Windows
While I originally made this for Linux but apparently MICROSOFT WINDOWS Users want to use this too. Here is a guide:
1. Download the executable from the latest release
2. Place in a folder you like and start it. It will create a config.ini
3. Open the config.ini and add your logpath
4. Restart the application. It should now be scanning the provided logpath for new logs created after the application was started.
## Having an extra Window open is annoying
That is tough. I personally park this on a hidden workspace. Windows has a similar feature called "Virtual Desktops" and you can access it with ```Windows + Tab```. Check out if you like it.
# Etc
Feel free to steal this for anything. Maybe I'll make it less scuffed in the future.<br>
Last tested with my python 3.7 setup on Arch Linux and the state of dps.report/wingman APIs as of 27.10.2023.
# Licenses of used packages
requests: Apache 2.0
psyimplegui: GNU LESSER GENERAL PUBLIC LICENSE
pyperclip: See licenses.txt
