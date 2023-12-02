# Scuffed little uploader
Threw it together because the official uploader doesn't work on Linux. Or maybe I'm just stupid.
Does nothing fancy, it watches for new logs and uploads them to dps.report and then adds that to the wingman queue.
```uploader.py``` is the CLI Version that I personally use. ```gui_version.py``` obviously is the GUI Version for the LESS STRONG MINDED people. 

# CLI Version
 ```pip install requests```
# GUI Version
This shit now has a GUI Version. Its bad and ugly, please improve it if you can. I've never made a GUI before and I still don't really want to. The GUI is multithreaded and there may be concurrency issues. I haven't found any but there may be. Packages required:\
```pip install requests pysimplegui pyperclip configparser```<br>
It is also possible to choose your own Theme by setting it in the generated .ini file. You can view all themes here:<br>
https://media.geeksforgeeks.org/wp-content/uploads/20200511200254/f19.jpg<br>
Example: ```theme = Dark Brown 3```
## config.ini
On first run the GUI Program will create a config.ini. You can specify a logpath in there if you want to. Ideally the path should have no spaces. The program checks all subfolders, so you can just specify your path to ```arcdps.cbtlogs```.
# How to use this on Windows
While I originally made this for Linux but apparently MICROSOFT WINDOWS Users want to use this too. Here is a guide:
1. Download the contents of this repo
2. Install Python. CHECK THE CHECKBOX THAT ASKS WHETHER YOU WANT TO ADD PYTHON TO YOUR PATH. YES YOU DO.
3. Open a Terminal (search for cmd in start menu) and run: ```pip install requests pysimplegui pyperclip configparser```
4. Move ```gui_version.py``` into your arcdps.cbtlogs folder. Doubleclick it.
5. An ugly GUI should open. There will also be a ```config.ini``` in the folder.<br>
__Alternatively: Use the .exe from the Release pages(available soonTM)__.
## Having an extra Window open is annoying
That is tough. I personally park this on a hidden workspace. Windows has a similar feature called "Virtual Desktops" and you can access it with ```Windows + Tab```. Check out if you like it.
# Etc
Feel free to steal this for anything. Maybe I'll make it less scuffed in the future.<br>
Last tested with my python 3.7 setup on Arch Linux and the state of dps.report/wingman APIs as of 27.10.2023.