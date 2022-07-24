import logging
from pathlib import Path
import random
import linecache
import os

class MentionDB:
    def __init__(self, db_id):
        self.strDBID = db_id
        self.LoadDB()

    def GetDBPath(self):
        return "".join(["./data/", self.strDBID, "_mentiondb", ".txt"])

    def LoadDB(self):
        logging.debug(" ".join([self.strDBID, "Mention DB Loading"]))

        sPath = self.GetDBPath()
        objDatabasePath = Path(sPath)

        if not objDatabasePath.is_file():
            self.RecreateDB()

    def RecreateDB(self):
        logging.debug(" ".join([self.strDBID, "Recreating Mention DB"]))

        sPath = self.GetDBPath()
        objDatabasePath = Path(sPath)

        if objDatabasePath.is_file():
            #delete
            objDatabasePath.unlink()
            logging.debug(" ".join([self.strDBID, "Mention DB found and deleted"]))

        with open(sPath, "w") as database:
            database.write("\n")

    def AddID(self, ID):
        logging.debug(" ".join([self.strDBID, "Writing ID", ID, "to Mention DB"]))

        #read file
        line_list = []
        with open(self.GetDBPath(), "r") as db:
            line_list = db.readlines()

        #rewrite file
        line_list.append("".join([ID,"\n"]))

        try:
            with open(self.GetDBPath(), "w") as db:
                db.writelines(line_list)
        except:
            logging.debug(" ".join([self.strDBID, "Error Appending to Mention DB"]))

    def CheckID(self, ID):

        line_list = []
        with open(self.GetDBPath(), "r") as db:
            line_list = db.readlines()

        for line in line_list:
            if line == ID:
                logging.debug(" ".join([self.strDBID, "Mention DB ID", ID, "is in DB"]))
                return true

        logging.debug(" ".join([self.strDBID, "Mention DB ID", ID, "is NOT in DB"]))
        return false


class ImagePathDB2:
    #inits/constructors/loaders/firsts
    def __init__(self, db_id, folders):
        self.strDBID = db_id
        self.aFolders = folders
        self.objDBSizes = {}
        self.objHighUsages = {}
        self.LoadDB()

    def RecreateDB(self):
        logging.debug(" ".join([self.strDBID, "Recreating Image DB"]))
        for folder in self.aFolders:
            self.RecreateDBForFolder(folder)

    def RecreateDBForFolder(self, folder):
        sPath = self.GetDBPathForFolder(folder)
        objDatabasePath = Path(sPath)

        #check and create file, otherwise delet
        if objDatabasePath.is_file():
            #delete
            objDatabasePath.unlink()
            logging.debug(" ".join([self.strDBID, "Image DB found and deleted"]))

        self.objDBSizes[folder] = 0
        self.objHighUsages[folder] = 0

        #open and dump new paths per folder
        try:
            with open(sPath, "w") as database:
                logging.debug(" ".join([self.strDBID, "Writing contents of:", sPath]))
                content_path = "".join(["./content/", folder])

                for item in Path(content_path).iterdir():
                    self.objDBSizes[folder] += 1
                    database.write("".join([str(item.absolute()),",0\n"])) #PATH, uses                
            logging.debug(" ".join([self.strDBID, "Created", folder, str(self.objDBSizes[folder])]))
        except:
            logging.debug(" ".join([self.strDBID, "Unable to create", folder]))



    def LoadDB(self):
        logging.debug(" ".join([self.strDBID, "Loading Image DB"]))
        for folder in self.aFolders:

            objDatabasePath = Path(self.GetDBPathForFolder(folder))

            if objDatabasePath.is_file():
                #check if theres stuff in there
                line_list = []
                with open(self.GetDBPathForFolder(folder), "r") as db:
                    line_list = db.readlines()

                if len(line_list) > 0:
                    #Read through file, get DBSize and HighUsages
                    logging.debug(" ".join([self.strDBID, "Loading", folder]))
                    nSize = 0
                    nHighUsage = 0

                    for line in line_list:
                        split_line = line.split(",")
                        nSize = nSize + 1
                        if( len(split_line) > 1 ):
                            if (int(split_line[1]) > nHighUsage):
                                nHighUsage = int(split_line[1])

                    self.objDBSizes[folder] = nSize
                    self.objHighUsages[folder] = nHighUsage
                    logging.debug(" ".join([self.strDBID, "Loaded", folder, str(nSize), str(nHighUsage)]))

                else:
                    logging.debug(" ".join([self.strDBID, "Error with ", self.GetDBPathForFolder(folder), " RECREATING"]))
                    self.RecreateDBForFolder(folder)

            elif not objDatabasePath.is_file():
                logging.debug(" ".join([self.strDBID, "Creating", self.GetDBPathForFolder(folder)]))
                self.RecreateDBForFolder(folder)

    def ClearDBUsesForFolder(self, folder):
        self.objHighUsages[folder] = 0

        for index in range(self.objDBSizes):
            self.UpdateDBByIDTo(index, folder, 0)

    #Updates
    def UpdateDBByID(self,ID, folder):
        #get current line
        nUsages = self.GetDBUsesByID(ID, folder)
        self.UpdateDBByIDTo(ID, folder, nUsages + 1)

    def UpdateDBByIDTo(self, ID, folder, value):
        #get current line
        strLine = self.GetDBStringByID(ID, folder)

        try:
            #read lines
            line_list = []
            with open(self.GetDBPathForFolder(folder), "r") as db:
                line_list = db.readlines()

            #update line usages
            split_line = line_list[ID].split(",")

            new_usage_value = value
            if new_usage_value > self.objHighUsages[folder]:
                self.objHighUsages[folder] = new_usage_value

            split_line[1] = "".join([str(new_usage_value), "\n"])

            new_line = ','.join(split_line)
            line_list[ID] = new_line

            #rewrite file
            with open(self.GetDBPathForFolder(folder), "w") as db:
                db.writelines(line_list)
        except:
            logging.debug(" ".join([self.strDBID, "Unable to to update DB folder -", folder, str(ID), str(value)]))


    #Randoms
    def GetRandomDBID(self, folder):
        nRandom = random.choice(range(self.objDBSizes[folder]))
        return nRandom

    def GetSomewhatRandomNotHighUsedDBID(self, folder):
        #try 5 times to get rando
        nRandomID = 0
        #print(" ".join(["Trying Random..."]))
        for random in range(5):
            nRandomID = self.GetRandomDBID(folder)
            nUsageCount = self.GetDBUsesByID(nRandomID, folder)
            #print("Uses", str(nUsageCount))
            if nUsageCount < self.objHighUsages[folder]:
                #print(" ".join(["Got: ", str(nRandomID)]))
                #we got it update and return
                self.UpdateDBByID(nRandomID, folder)
                return nRandomID

        #ok, get random value and iterate down until we find one?
        #print(" ".join(["Trying iterate from last..."]))
        while nRandomID < self.objDBSizes[folder] - 1:
            nRandomID += 1
            nUsageCount = self.GetDBUsesByID(nRandomID, folder)
            if nUsageCount <= self.objHighUsages[folder]:
                #print(" ".join(["Got: ", str(nRandomID)]))
                #we got it update and return
                self.UpdateDBByID(nRandomID, folder)
                return nRandomID

        #iterate from the top...
        #print(" ".join(["Iterate from the top..."]))
        for index in range(self.objDBSizes[folder]):
            nUsageCount = self.GetDBUsesByID(nRandomID, folder)
            if nUsageCount <= self.objHighUsages[folder]:
                #print(" ".join(["Got: ", str(nRandomID)]))
                #we got it update and return
                self.UpdateDBByID(nRandomID, folder)
                return nRandomID

        #fuck it up because something is fucked
        self.ClearDBUsesForFolder(folder)
        #nRandomID = self.GetRandomDBID()
        #print(" ".join(["Cleared and got", str(nRandomID)]))
        return nRandomID

    #DB Utils
    def GetDBPathByID(self, ID, folder):
        return self.GetDBStringByID(ID, folder).split(",")[0]
    def GetDBUsesByID(self, ID, folder):
        return int(self.GetDBStringByID(ID, folder).split(",")[1])
    def GetDBStringByID(self, ID, folder):
        toReturn = linecache.getline(self.GetDBPathForFolder(folder), ID + 1) #linecache starts at 1 for some reason...
        linecache.clearcache() #you also have to clear the cache if you want to load fresh for next time
        return toReturn

    def CheckDBIDValidity(self, ID, folder):
        #read lines
        line_list = []
        with open(self.GetDBPathForFolder(folder), "r") as db:
            line_list = db.readlines()

        return self.CheckDBStringValidity(line_list[ID])

    def CheckDBStringValidity(self, string):
        return len(string.split()) > 1

    #String Utils
    def GetDBPathForFolder(self, folder):
        return "".join(["./data/", self.strDBID, "_", folder, "_pathdb", ".txt"])

    #Debugging/Testing
    def STATS(self, folder):
        with open(self.GetDBPathForFolder(folder), "r") as db:
            line_list = db.readlines()
            for index in range(self.nDBSize):
                line = line_list[index]

        for index in range(self.nDBSize):
            print(" ".join([ "Index:", str(index), "-", self.GetDBStringByID(index, folder) ]))

    def SHOW_DB(self, folder):
        line_list = []
        with open(self.GetDBPathForFolder(folder), "r") as db:
            line_list = db.readlines()

        for line in line_list:
            print(line)