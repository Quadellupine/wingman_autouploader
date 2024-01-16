import requests
import sys
import csv
input_file = sys.argv[1]
encounter = sys.argv[2]
offset = sys.argv[3]
skill_id = sys.argv[4]

# Ignore this file, this is for a very specific usecase that YOU probably do not want to know about!!! do NOT ask me about this

def get_skillname_from_id(id):
    url = "https://api.guildwars2.com//v2/skills/"+id
    response = requests.get(url)
    content = response.json()
    return content["name"]

def parse_log(dps_link):
    return_values = []
    try:
        url = "https://dps.report/getJson?permalink="+dps_link
        response = requests.get(url)
        content = response.json()
        players = content["players"]
        # Dont touch it
        for player in players:
            damageDist = player["targetDamageDist"]
            for damages in damageDist:
                damages = damages[0]
                for item in damages:
                    if item["id"] == int(skill_id):
                        return_values.append(item["connectedHits"])
    except:
        print("error lmao")
        exit(1)
    return return_values


data = ["hits","offset", "encounter"]
f = open(input_file, "r")
lines = f.readlines()
hits = []
for line in lines:
    return_value = parse_log(line)
    for number in return_value:
        hits.append([number, offset, encounter])
skill = get_skillname_from_id(skill_id).replace(" ","_")
filename = encounter+"_offset_"+offset+"_"+skill+".csv"
with open(filename, "w") as fs:
    write = csv.writer(fs)
    write.writerow(data)
    write.writerows(hits)



    