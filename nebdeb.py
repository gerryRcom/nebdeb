#!/usr/bin/python3
import subprocess
import hashlib
import shutil
import os
import csv
import re
import datetime


# Set some constants for the source/ destination of all required/ generated content
INPUT = "input/"
OUTPUT = "output/"

# Some more relative constants
SYSTEMS = INPUT+"systems.csv"
BINHASH = INPUT+"binhash"
LHIP = "1"


# check for a specific file/ folder and return true or false
def checkExists(toCheck):
    if os.path.exists(toCheck):
        return True
    else:
        return False

# get date-time-stamp in preferred format, mostly used in log output
def getDateTime():
    timeStamp = datetime.datetime.now()
    return(timeStamp.strftime("%Y-%m-%d-%H:%M:%S"))

# log activity to output location as final version will not be run interactively
def logIt(logInput):
    nebdebLog=OUTPUT+"nebdeb.log"
    if os.path.exists(nebdebLog):
        try:
            with open(nebdebLog, 'at') as nebdebLogContent:
                nebdebLogContent.write(getDateTime()+","+logInput+"\n")
                nebdebLogContent.close()
        except:
            print("error, unable to write to log file in output folder")
    else:
        try:
            with open(nebdebLog, 'wt') as nebdebLogContent:
                nebdebLogContent.write(getDateTime()+","+logInput+"\n")
                nebdebLogContent.close()
        except:
            print("error, unable to create log file in output folder")



# generate certs, this assumes the CA cert and key have already been genrated, default action creates host certs but doesn't overwrite them if they exist
# this is useful if we need to rebuild deb due to new nebula binary we can just add the new binary, re-generate and the existing certs will be retained
def generateCert(hostName, nebIP):
    logIt("generating cert,"+hostName+","+nebIP)
    certCommand=INPUT+"/certs/nebula-cert sign -ca-crt "+INPUT+"certs/ca.crt -ca-key "+INPUT+"certs/ca.key -name "+hostName+" -ip "+nebIP+"/24 -out-crt "+OUTPUT+hostName+"/nebula/usr/bin/nebula/"+hostName+".crt -out-key "+OUTPUT+hostName+"/nebula/usr/bin/nebula/"+hostName+".key"
    ##print(certCommand)
    print(subprocess.call(certCommand, shell=True))
    logIt("cert generatetion complete,"+hostName+","+nebIP)


# Get the hash of a file to compare against previous version
def getHash(fileName):
    if os.path.exists(INPUT+fileName):
        logIt("getting file hash for,"+fileName)
        with open(INPUT+fileName, 'rb') as fileBinary:
            fileBinaryContent = fileBinary.read()
            return hashlib.sha256(fileBinaryContent).hexdigest()
    else:
        logIt("unable to get file hash for,"+fileName)


# Compare hash of current file to previous known hash, update known hash value if it's different
# true/ false return will be used to determine if rebuild is required
def compareHash(hashToCompare):
    hashToComparePath = INPUT+hashToCompare
    if os.path.exists(hashToComparePath):
        logIt("getting file hash for,"+hashToComparePath)
        with open(hashToComparePath, 'rt') as fileHash:
            fileHashContent = fileHash.read()
            fileHash.close()
            if fileHashContent == getHash(hashToComparePath):
                logIt("hash has not changed for,"+hashToComparePath)
                return True
            else:
                with open(hashToComparePath, 'wt') as fileHash:
                    logIt("updating hash for,"+hashToComparePath)
                    fileHash.write(getHash(hashToComparePath))
                    fileHash.close()
                    return False
    else:
        logIt("unable to get file hash for,"+hashToCompare)

# build nebula config file per host
def buildConfig(hostName,nebIP,amLighthouse,lightHouse):
    # Define placeholder entries
    PH_HOST="##HOSTNAME##"
    PH_IP="##HOSTIP##"
    PH_AMLIGHTHOUSE="##AMLIGHTHOUSE##"
    PH_LIGHTHOUSE="##LIGHTHOUSE##"
    PH_LIGHTHOUSEIP="##LIGHTHOUSEIP##"
    PH_LIGHTHOUSEHOST="##LIGHTHOUSEHOST##"
    PH_PORT="##LISTENPORT##"

    # Get the IP of the lighthouse using the network address and the LHIP constant
    lightHouseIP = re.sub(r'\d{1,3}$',LHIP,nebIP)

    os.makedirs(OUTPUT+hostName,exist_ok=True)
    shutil.copyfile(INPUT+'nebula.yml', OUTPUT+hostName+'/'+hostName+'.yml')

    # read in the nebula template, substitute placeholders and output host's nebula config file
    with open(OUTPUT+hostName+'/'+hostName+'.yml', 'rt') as configFile:
        configData = configFile.read()
        configData = configData.replace(PH_HOST, hostName)
        configData = configData.replace(PH_IP, nebIP)
        configData = configData.replace(PH_LIGHTHOUSE, lightHouse)
        configData = configData.replace(PH_AMLIGHTHOUSE, amLighthouse)
        configData = configData.replace(PH_LIGHTHOUSEIP, lightHouseIP)
        if amLighthouse == "true":
            configData = configData.replace(PH_PORT, "4242")
            configData = configData.replace(PH_LIGHTHOUSEHOST, "")
        else:
            configData = configData.replace(PH_PORT, "0")
            configData = configData.replace(PH_LIGHTHOUSEHOST, "- \""+lightHouseIP+"\"")
        configFile.close()
    with open(OUTPUT+hostName+'/'+hostName+'.yml', 'wt') as configFile:
        configFile.write(configData)
        configFile.close()

# build linux service file per host
def buildService(hostName):
    # Define placeholder entries
    PH_HOST="##HOSTNAME##"
    shutil.copyfile(INPUT+'nebula.service', OUTPUT+hostName+'/nebula.service')

    # read in the service template, substitute placeholders and output host's service file
    with open(OUTPUT+hostName+'/nebula.service', 'rt') as serviceFile:
        serviceData = serviceFile.read()
        serviceData = serviceData.replace(PH_HOST, hostName)
        serviceFile.close()
    with open(OUTPUT+hostName+'/nebula.service', 'wt') as serviceFile:
        serviceFile.write(serviceData)
        serviceFile.close()

# build deb package per host
def buildDeb(hostName):
    # build folder and file structure for the .deb
    os.makedirs(OUTPUT+hostName+'/nebula/',exist_ok=True)
    os.makedirs(OUTPUT+hostName+'/nebula/usr/bin/nebula/',exist_ok=True)
    os.makedirs(OUTPUT+hostName+'/nebula/etc/systemd/system/',exist_ok=True)
    shutil.copytree(INPUT+'DEB', OUTPUT+hostName+'/nebula/', dirs_exist_ok=True)
    shutil.copy2(INPUT+'nebula', OUTPUT+hostName+'/nebula/usr/bin/nebula/nebula')
    shutil.copy2(INPUT+'certs/ca.crt', OUTPUT+hostName+'/nebula/usr/bin/nebula/ca.crt')
    shutil.copy2(OUTPUT+hostName+'/nebula.service', OUTPUT+hostName+'/nebula/etc/systemd/system/nebula.service')
    shutil.copy2(OUTPUT+hostName+'/'+hostName+'.yml', OUTPUT+hostName+'/nebula/usr/bin/nebula/'+hostName+'.yml')

    # build deb package from content generated above
    debCommand="dpkg-deb --build --root-owner-group "+OUTPUT+hostName+"/nebula"
    print(debCommand)
    print(subprocess.call(debCommand, shell=True))

# purge all previously generated output e.g. if a cert was exposed or you a new binary was released.
def purgeOutput(toPurge):
    if toPurge == "1":
        shutil.rmtree(OUTPUT)


def nebdebMenu():
    print("################################")
    print("##   nebdeb - Manage Nebula   ##")
    print("##                            ##")
    print("##   1 - Purge All Output     ##")
    print("##   2 - List Systems in csv  ##")
    print("##   3 - List Systems Output  ##")
    print("##   4 - Generate configs     ##")
    print("##                            ##")
    print("##   5 - Exit                 ##")
    print("##                            ##")
    print("################################")


if __name__ == "__main__":
    #buildConfig("testbane","199.222.222.222","false","1.1.1.1")
    #buildService("testbane")

    logIt("testRun")

    """  
    with open(INPUT+'systems.csv', newline='') as systemsCSV:
        systemsContent = csv.reader(systemsCSV)
        # skip header line
        next(systemsContent, None)



        # print menu while waiting for input from user
        nebdebMenu()
        print("Enter selection 1-5: ")
        menuSelection = input()
        if menuSelection == "1":
            purgeOutput(menuSelection)
        elif menuSelection == "2":
            for systemsData in systemsContent:
                print(systemsData[0],systemsData[1],systemsData[2],systemsData[3])
        elif menuSelection == "3":
            print(os.listdir(OUTPUT))
        elif menuSelection == "4":
            for systemsData in systemsContent:
                buildConfig(systemsData[0],systemsData[1],systemsData[2],systemsData[3])
                buildService(systemsData[0])
                # first run create folder structure for cert generation TODO - improve on this
                buildDeb(systemsData[0])
                generateCert(systemsData[0],systemsData[1])
                buildDeb(systemsData[0])
        elif menuSelection == "5":
            exit()
        else:
            print("Invalid selection")
        """