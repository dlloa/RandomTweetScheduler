import twatv2
import json
import time
from time import struct_time
import random
from pathlib import Path

#Current Times
nWeekday = 999
nLastUpdateHour = 999
nLastUpdateMin = 999

#Settings
GMT_OFFSET = -8
TEST = 0
Accounts = []


#"Time": {
#    "EveryMin": "15",
#    "Hour":     "*",
#    "Minute":   "15"
#},
# EverMin would be mod EverMin
# * will wildcard for Hour
def isTime(objTime):
    global nLastUpdateHour
    global nLastUpdateMin

    #Get if time is corrent from Rule Data
    bIsTime = 0
    if objTime.get("EveryMin", 0) != 0:
        bIsTime = (nLastUpdateMin % int(objTime.get("EveryMin", "1"))) == 0
    else:
        bHourCorrect = 0
        bMinCorrect = 0

        strHour = objTime.get("Hour", "*")
        strMin = objTime.get("Minute", "0")

        if strHour == "*" or int(strHour) == nLastUpdateHour:
            bHourCorrect = 1
        if int(strMin) == nLastUpdateMin:
            bMinCorrect = 1
        bIsTime = bHourCorrect and bMinCorrect

    #No post on 0 minutes
    if objTime.get("Zero", 1) == 0:
        if nLastUpdateMin == 0:
            bIsTime = 0 and 1

    return bIsTime

def handleTime(objTime):
    #New time?
    global nLastUpdateHour
    global nLastUpdateMin
    global nWeekday
    if (nLastUpdateHour != objTime.tm_hour) or (nLastUpdateMin != objTime.tm_min):
        nLastUpdateHour = objTime.tm_hour
        nLastUpdateMin = objTime.tm_min
        nWeekday = objTime.tm_wday
        return 1
    return 0

def checkTimes(aTimeData):
    bToReturn = 0
    for item in aTimeData:
        if isTime(item):
            bToReturn = isTime(item)
    return bToReturn

#Load all settings files in settings folder
for item in Path("./settings").iterdir():
    with open(item, "r") as f:
        objSettings = json.loads(f.read())
        strConsumerKey = objSettings["Settings"]["ConsumerKey"];
        strConsumerSecret = objSettings["Settings"]["ConsumerSecret"];
        for user in objSettings["Users"]:
            bActive = bool(int(user["Active"]))
            strID = user["ID"]
            strToken = user["TokenKey"]
            strSecret = user["TokenSecret"]
            aFolders = user["Folders"]
            objRules = user["PostRules"]
            newuser = twatv2.TwitterAuth(bActive, strID, strToken, strSecret, strConsumerKey, strConsumerSecret, aFolders, objRules)
            Accounts.append(newuser)

twatv2.logging.debug(" ".join(["All users created"]))

while 1:      
    time.sleep(10)
    if (handleTime(time.localtime(time.time()))):
        twatv2.logging.debug(" - ".join([str(nWeekday), str(nLastUpdateHour), str(nLastUpdateMin)]))

        for acc in Accounts:
            if acc._bActive:
                for rule in acc._aRules:
                    
                    #Load Data if its there
                    strID = rule.get("ID", "NONE")
                    aTimes = rule.get("Time", [])
                    objData = rule.get("Data", {})

                    if checkTimes(aTimes):
                        if acc.TestFolders():
                            nWeekdayToPost = int(objData.get("Weekday", nWeekday))
                            if nWeekdayToPost == nWeekday:
                                print(" ".join([acc._strID, strID]))

                                #load from objData
                                aMessages = objData.get("Messages", [])
                                aMentions = objData.get("Mentions", [])
                                nTagCount = objData.get("TagCount", 5) #int or "ALL"
                                aTags = objData.get("Tags", [])
                                nPicAmount = objData.get("Amount", 1)
                                aFolders = objData.get("Folders", [])

                                #get message
                                strMessageToPost = random.choice(aMessages)

                                #get tags
                                aTagsToPost = []
                                if len(aTags):
                                    if nTagCount == "ALL":
                                        aTagsToPost = aTags
                                    else:
                                        aTagsToPost = random.choices(aTags, k=nTagCount)

                                #get mentions
                                aMentionsToPost = aMentions

                                #combine message
                                strMentionsToPost = " ".join(aMentionsToPost)
                                strTagsToPost = " ".join(aTagsToPost)
                                strMessageToPost = " ".join([strMessageToPost, strMentionsToPost, strTagsToPost])

                                acc.TweetRandomMediaFromFolders(strMessage=strMessageToPost, aFolders=aFolders, nNum=nPicAmount)
                        else:
                            twatv2.logging.debug(" ".join(["Error with Folders, rebooting"]))
                            twatv2.os.system("sudo shutdown -r now")
##
##
##
##
##
##
##
##