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
        logIt("confirmed the path,"+toCheck)
        return True
    else:
        logIt("no such path,"+toCheck)
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
    if checkExists(INPUT+"/certs/nebula-cert sign"):
        logIt("generating cert,"+hostName+","+nebIP)
        certCommand=INPUT+"/certs/nebula-cert sign -ca-crt "+INPUT+"certs/ca.crt -ca-key "+INPUT+"certs/ca.key -name "+hostName+" -ip "+nebIP+"/24 -out-crt "+OUTPUT+hostName+"/nebula/usr/bin/nebula/"+hostName+".crt -out-key "+OUTPUT+hostName+"/nebula/usr/bin/nebula/"+hostName+".key"
        ##print(certCommand)
        print(subprocess.call(certCommand, shell=True))
        logIt("cert generatetion complete,"+hostName+","+nebIP)
    else:
        exit()


# Get the hash of the nebula binary to comapre against previous run
def getHash():
    if os.path.exists(INPUT+"nebula"):
        logIt("getting file hash for nebula")
        with open(INPUT+'nebula', 'rb') as nebulaBinary:
            nebulaBinaryContent = nebulaBinary.read()
            return hashlib.sha256(nebulaBinaryContent).hexdigest()
    else:
        logIt("unable to get file hash for nebula")
        exit()

## Compare hash of current binary to previous known hash, update known hash value if it's different
# true/ false return will be used to determine if rebuild is required
def compareHash():
    if os.path.exists(BINHASH):
        logIt("getting file hash for nebula to compare")
        with open(BINHASH, 'rt') as nebulaHash:
            nebulaHashContent = nebulaHash.read()
            nebulaHash.close()
            logIt("comparing hash with known hash")
            if nebulaHashContent == getHash():
                logIt("hash has not changed")
                return True
            else:
                logIt("hash has changed")
                with open(BINHASH, 'wt') as nebulaHash:
                    logIt("updating known hash")
                    nebulaHash.write(getHash())
                    nebulaHash.close()
                    return False
    else:
        # save the hash for next run if no hash was found
        logIt("unable to get file hash for to compare")
        with open(BINHASH, 'wt') as nebulaHash:
            logIt("saving current hash")
            nebulaHash.write(getHash())
            nebulaHash.close()
            return False

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
    try:
        os.makedirs(OUTPUT+hostName+'/nebula/',exist_ok=True)
        os.makedirs(OUTPUT+hostName+'/nebula/usr/bin/nebula/',exist_ok=True)
        os.makedirs(OUTPUT+hostName+'/nebula/etc/systemd/system/',exist_ok=True)
        shutil.copytree(INPUT+'DEB', OUTPUT+hostName+'/nebula/', dirs_exist_ok=True)
        shutil.copy2(INPUT+'nebula', OUTPUT+hostName+'/nebula/usr/bin/nebula/nebula')
        shutil.copy2(INPUT+'certs/ca.crt', OUTPUT+hostName+'/nebula/usr/bin/nebula/ca.crt')
        shutil.copy2(OUTPUT+hostName+'/nebula.service', OUTPUT+hostName+'/nebula/etc/systemd/system/nebula.service')
        shutil.copy2(OUTPUT+hostName+'/'+hostName+'.yml', OUTPUT+hostName+'/nebula/usr/bin/nebula/'+hostName+'.yml')
    except:
        print("error, unable to locate content when copying to {1} output folder"+hostName)
        exit()
    # build deb package from content generated above
    debCommand="dpkg-deb --build --root-owner-group "+OUTPUT+hostName+"/nebula"
    print(debCommand)
    print(subprocess.call(debCommand, shell=True))

# purge all previously generated output e.g. if a cert was exposed or you a new binary was released.
def purgeOutput():
    logIt("purging all output")
    shutil.rmtree(OUTPUT)

if __name__ == "__main__":
    #buildConfig("testbane","199.222.222.222","false","1.1.1.1")
    #buildService("testbane")
    toPurge = ""
    logIt("check if required to purge all existing output")
    if os.path.exists(INPUT+"purgeall"):
        purgeOutput()
        logIt("resetting purge request")
        os.remove(INPUT+"purgeall")
        toPurge = "yes"
    else:
        logIt("no request to purge content found")
        toPurge = "no"

    # If flag to purge was reeived or if the nebula binary changed, re-build all host configs.
    if not compareHash() or toPurge == "yes":
        logIt("proceeding to rebuild all host configs")
        logIt("opening systems.csv for host data")
        if os.path.exists(SYSTEMS):
            with open(SYSTEMS, newline='') as systemsCSV:
                systemsContent = csv.reader(systemsCSV)
                # skip header line
                next(systemsContent, None)
                logIt("iterating through hosts")
                for systemsData in systemsContent:
                    logIt("building config for host,"+systemsData[0])
                    buildConfig(systemsData[0],systemsData[1],systemsData[2],systemsData[3])
                    logIt("building service file for host,"+systemsData[0])
                    buildService(systemsData[0])
                    # first run create folder structure for cert generation TODO - improve on this
                    logIt("building deb structure for host,"+systemsData[0])
                    buildDeb(systemsData[0])
                    logIt("generating cert for host,"+systemsData[0])
                    generateCert(systemsData[0],systemsData[1])
                    logIt("building deb for host,"+systemsData[0])
                    buildDeb(systemsData[0])
        else:
            logIt("unable to open systems.csv file")
    # If flag to purge was not received and if the nebula binary has not change, only buold hosts that do not have an existing output
    else:
        logIt("building host config if no output found")
        logIt("opening systems.csv for host data")
        if os.path.exists(SYSTEMS):
            with open(SYSTEMS, newline='') as systemsCSV:
                systemsContent = csv.reader(systemsCSV)
                # skip header line
                next(systemsContent, None)
                for systemsData in systemsContent:
                    logIt("checking for output content for host,"+systemsData[0])
                    if not checkExists(OUTPUT+systemsData[0]):
                        logIt("no existing output found for host,"+systemsData[0])
                        logIt("building config for host,"+systemsData[0])
                        buildConfig(systemsData[0],systemsData[1],systemsData[2],systemsData[3])
                        logIt("building service file for host,"+systemsData[0])
                        buildService(systemsData[0])
                        # first run create folder structure for cert generation TODO - improve on this
                        logIt("building deb structure for host,"+systemsData[0])
                        buildDeb(systemsData[0])
                        logIt("generating cert for host,"+systemsData[0])
                        generateCert(systemsData[0],systemsData[1])
                        logIt("building deb for host,"+systemsData[0])
                        buildDeb(systemsData[0])
                    else:
                        logIt("existing output content found for host,"+systemsData[0])
        else:
            logIt("unable to open systems.csv file")
