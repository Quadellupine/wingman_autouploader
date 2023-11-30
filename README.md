# Scuffed little uploader
Therw it together because the official uploader doesnt work on Linux. Or maybe Im just stupid.
Does nothing fancy, it watches for new logs and uploads them to dps.report and then adds that to the wingman queue.

To use it all you need to do is\
 ```pip install requests```\
(I think)
# GUI Version
This shit now has a GUI Version. Its bad and ugly, please improve it if you can. Ive never made a GUI before and I still dont really want to.\
# How to use this on Windows
While I originally made this for Linux apparently MICROSOFT WINDOWS Users want to use this too. Here is a guide:\
1. Download the contents of this repo
2. Install Python. CHECK THE CHECKBOX THAT ASKS WHETHER YOU WANT TO ADD PYTHON TO YOUR PATH. YES YOU DO.
3. Open a Terminal (search for cmd in start menu) and run: ```pip install requests pysimplegui pyperclip configparser```
4. MMove ```guiversion.py``` into your arcdps.cbtlogs folder. Doubleclick it.
5. An ugly GUI should open. There will also be a ```config.ini``` in the folder.
# Etc
Feel free to steal this for anything. Maybe Ill make it less scuffed in the future.\
Last tested with my python 3.7 setup on Arch Linux and the state of dps.report/wingman APIs as of 27.10.2023.