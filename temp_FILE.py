import json
import os
from pprint import pprint
import csv

csvpath = 'userCSV.csv'
jsonPath = 'userJSON.json'
csvData = None

subredditDict = dict()
allSubs = set()

with open(csvpath) as csvFile:
    csvData = csv.reader(csvFile, delimiter=',')
    for row in csvData:
        try:
            username = row.pop(0)
            subreddits = set(row)
            if username not in subredditDict:
                subredditDict[username] = subreddits
            else:
                subredditDict[username].update(subreddits)
            allSubs.update(subreddits)
        except Exception as e:
            pass
        subredditDict[username] = list(subredditDict[username])
print(type(subredditDict))
pprint(subredditDict)
with open(jsonPath, 'w') as jsonfile:
    json.dump(subredditDict, jsonfile, indent=4)
