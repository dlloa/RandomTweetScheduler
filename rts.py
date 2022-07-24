import sys
import os
import time
from time import struct_time
import random
#from pathlib import Path
from enum import Enum

import logging
import shelve
import json
import linecache

from twitter import *

logging.basicConfig(filename='log', filemode='a',level=logging.DEBUG, format=' %(asctime)s -%(levelname)s - %(message)s')
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

import db

class TwitterAuth:
    def __init__(self, active, ID, token, token_secret, consumer_key, consumer_secret, folders, postrules):
        self._bActive = active
        self._strID = ID

        self.token = token;
        self.token_secret = token_secret
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        self._aRules = postrules
        self._aFolders = folders
        self._objImageDB = db.ImagePathDB2( self._strID, self._aFolders )

        #Find/Create Credentials (Will ask to log in)
        credentials_path = "".join(["./data/",self._strID,"_creds",".txt"])
        credentials_path = os.path.expanduser(credentials_path)
        if not os.path.exists(credentials_path):
            oauth_dance("HentaiLeBot", self.consumer_key, self.consumer_secret,
                        credentials_path)
        oauth_token, oauth_secret = read_token_file(credentials_path)

        #Create Objects with Creds
        self._objAuth = OAuth(oauth_token, oauth_secret, self.consumer_key, self.consumer_secret)
        self._objTwitter = Twitter( auth=self._objAuth )
        self._objMedia = Twitter( domain="upload.twitter.com", auth=self._objAuth )

        logging.debug(" ".join(["User", ID, "data collected and object created"]))

    #Upload to Twitter, returns Image IDs for tweet attach
    def UploadMedia(self, aPaths):
        toReturnIDs = []

        #We want to strip the paths down to one r if there is one in there...
        for path in aPaths:
            split_path = path.split(".")
            if( split_path[-1].lower() == "gif" ):
                aPaths = [path]
                break

        for path in aPaths:
            with open(path.strip(), "rb") as imagefile:
                logging.debug(" ".join(["Uploading ", path.strip()]))

                for i in range(0, 3):
                    try:
                        #Upload and get image ID, append
                        image_id = self._objMedia.media.upload(media=imagefile.read())["media_id_string"]
                        logging.debug(" ".join(["Uploaded - ", image_id]))
                        toReturnIDs.append(image_id)
                    except Exception as err:
                        logging.debug(" ".join([str(err)]))
                        logging.debug(" ".join(["Error uploading, attempt", str(i)]))
                        continue
                    break

        return toReturnIDs

    #Tweet Message with Image IDs
    def TweetWithMediaIDs(self, strMessage="", aMediaIDS=[]):
        logging.debug(" ".join(["Tweeting \'", strMessage, "\' with: ", ",".join(aMediaIDS)]))
        
        for i in range(0, 3):
            try:
                self._objTwitter.statuses.update(status=strMessage, media_ids=",".join(aMediaIDS))
                logging.debug(" ".join(["Tweeted!"]))
                return 1
            except Exception as err:
                logging.debug(" ".join([str(err)]))
                logging.debug(" ".join(["Tweet Error, attempt", str(i)]))
                continue
            break
        return 0

    #Upload media at objPaths and Tweet Message and Media
    def TweetWithMedia(self, strMessage="", objPaths=[]):
        objMediaIDS = self.UploadMedia(objPaths)
        if( len(objMediaIDS) > 0 ):
            return self.TweetWithMediaIDs(strMessage, objMediaIDS)
        else:
            logging.debug(" ".join(["No Uploaded Images, skipping Tweet"]))
            return 0

    #Choose random folder and TweetWithMedia
    def TweetRandomMedia(self, strMessage="", nNum = 1):
        folder = random.choice(self._aFolders)
        paths = []

        for i in range(nNum):
            path = self.GetRandomPathFromDB(folder)
            paths.append(path)

        strMessage = self.AppendTagListToMessage(folder, strMessage)    
        return self.TweetWithMedia(strMessage, paths)

    #Choose random folder from given aFolders and TweetWithMedia
    def TweetRandomMediaFromFolders(self, strMessage="", aFolders=[], nNum = 1):
        for i in range(3):
            if len(aFolders) > 0:
                folder = random.choice(aFolders)
                paths = []

                for i in range(nNum):
                    path = self.GetRandomPathFromDB(folder)
                    paths.append(path)

                strMessage = self.AppendTagListToMessage(folder, strMessage)

                if self.TweetWithMedia(strMessage, paths) == 1:
                    break
            else:
                if self.TweetRandomMedia(strMessage, nNum) == 1:
                    break

    #Tweet Utils
    def AppendTagListToMessage(self, folder, strMessage):
        #add tags to message if they exist
        aTagsFromFolder = self.GetTagList(folder)
        if( len(aTagsFromFolder) > 0 ):
            sTags = ""
            for tag in aTagsFromFolder:
                sTags = sTags + " " + tag.rstrip('\n')

            strMessage = strMessage + " " + sTags

        return strMessage

    #DB Utils
    def RecreateDB(self):
        self._objImageDB.RecreateDB()
    def GetDBPath(self):
        return "".join(["./data/",self._strID,"_pathdb",".txt"])
    def GetRandomPathFromDB(self, folder):
        randomID = self._objImageDB.GetSomewhatRandomNotHighUsedDBID(folder)
        randomPath = self._objImageDB.GetDBPathByID(randomID, folder)
        return randomPath

    #File Utils
    def GetPathList(self):
        aPaths = []

        for folder in self._aFolders:
            aPaths.append("".join(["./content/", folder]))

        return aPaths

    def GetTagList(self, folder):
        aTags = []
        sTagFile = "".join(["./content/", folder, "/", "tags.txt"])

        try:
            with open(sTagFile, "r") as db:
                aTags = db.readlines()
        except Exception as err:
            print(err)

        return aTags

    def TestFolders(self):
        for folder in self._aFolders:
            if not os.path.isdir("".join(["./content/", folder])):
                return 0

        return 1

    #Trash
    def JSONGet(self, objJSON, aPath):
        toReturn = objJSON
        for path in aPath:
            toReturn = toReturn.get(path, "ERROR")
        return toReturn

    #Get Latest Tweet in Home Timeline
    #Check to see if we have any @Mentions to us
    #If we do have an @Mention that is not part of the DB
    #Add to Mention DB (text doc, each line is unique id from tweet)
    #Itertate through Hastags to see if we have a match in Folders
    #If we do, post random media from that folder
    #def AutoReplyWithFolders(self):
    def RTCheck(self):
        for tweet in self._objTwitter.statuses.user_timeline(screen_name=self._strID, count=10):
            if tweet.get("retweeted", 0):
                print(tweet.get("retweet_count"))
                #for item in (self._objTwitter.statuses.show(_id=tweet.get("id"))).get("retweeted_status"):
                    #print(item)
                break

                #if item.get("id_str", "ERROR") == self._strID:
                #    print(self._objTwitter.statuses.show(_id=item.get("id")))
                #for twt_item in item:
                #    print(twt_item.get())
                #break


            #for twt_item in item.get("extended_entities"):
            #for twt_item in item:
            #    print(twt_item)

    def TimeLineCheck(self):
        #ht = self._objTwitter.statuses.home_timeline()
        #print(ht[0]["retweeted"])
        #for item in ht[0]:
        #    print(item)

        #Unique ID for Each Tweet (STRING)
        #item.get("id", "ERROR")

        #User Mentions (LIST), screen_name to match ID
        #item.get("entities", "ERROR").get("user_mentions", "ERROR")
        #item.get("entities", "ERROR").get("user_mentions", "ERROR")[-X-].get("screen_name", "ERROR")

        #Hashtags (LIST), text to match for 
        #item.get("entities", "ERROR").get("hashtags", "ERROR")
        #item.get("entities", "ERROR").get("hashtags", "ERROR")[-X-].get("text", "ERROR")

        #for item in self._objTwitter.statuses.user_timeline(screen_name=self._strID, count=1):
        for item in self._objTwitter.statuses.home_timeline(count=100):
            if( (item.get("user", "ERROR")).get("screen_name", "ERROR") == "Hentai_Le"):
                if( len(item.get("entities", "ERROR").get("user_mentions", "ERROR")) > 0 ):
                    print(item.get("id", "ERROR"))
                    #for user in item.get("entities", "ERROR").get("user_mentions", "ERROR"):
                    print(item.get("entities", "ERROR"))
                    break

            #if( (item.get("user", "ERROR")).get("screen_name", "ERROR") == "Hentai_Le"):
            #    for thing in item["entities"]:
            #        print(thing)
            #    print("\n")
            #    print(item)
            #    print("\n")
            #    print(item.get("user", "ERROR"))
            #    print(item.get("text", "ERROR"))
            #    print(item.get("entities", "ERROR").get("user_mentions","ERROR"))
            #    print("\n")
            #    print(self.JSONGet(item, ["entities", "user_mentions", "name"]))
            #    break;
            #print("\n")
            #for thing in item:
            #    print(thing)
            #if item["retweeted"]:
            #    print("\n")
            #    for thing in item:
            #        print(thing)
            #    print("\n")
            #    print(item["retweeted_status"])
            #    #for thing in item:
            #    #    print(thing)
            #    break


#
#
#
#
#
#
#
#