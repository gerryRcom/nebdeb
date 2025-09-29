#!/usr/bin/python3
import subprocess
import hashlib
import shutil
import os
import csv


# Set some constants
SYSTEMS = "input/systems.csv"
INPUT = "input/"
OUTPUT = "output/"
BINHASH = "input/binhash"



def generateCert(hostName, nebIP):
    certCommand=INPUT+"nebula-cert sign -name "+hostName+" -ip "+nebIP
    print(certCommand)
    print(subprocess.call(certCommand, shell=True))

# Get the hash of the nebula binary to comapre against previous run
def getHash():
    with open(INPUT+'nebula', 'rb') as nebulaBinary:
        nebulaBinaryContent = nebulaBinary.read()
        return hashlib.sha256(nebulaBinaryContent).hexdigest()

# Compare hash of current binary to previous known hash, update known hash value if it's different
# true/ false return will be used to determine if rebuild is required
def compareHash():
    with open(BINHASH, 'rt') as nebulaHash:
        nebulaHashContent = nebulaHash.read()
        nebulaHash.close()
        if nebulaHashContent == getHash():
            return True
        else:
            with open(BINHASH, 'wt') as nebulaHash:
                nebulaHash.write(getHash())
                nebulaHash.close()
                return False

def buildConfig(hostName,nebIP,amLighthouse,lightHouse):
    # Define placeholder entries
    PH_HOST="##HOSTNAME##"
    PH_IP="##HOSTIP##"
    PH_AMLIGHTHOUSE="##AMLIGHTHOUSE##"
    PH_LIGHTHOUSE="##LIGHTHOUSE##"

    os.makedirs(OUTPUT+hostName,exist_ok=True)
    shutil.copyfile(INPUT+'nebula.yml', OUTPUT+hostName+'/'+hostName+'.yml')

    # read in the nebula template, substitute placeholders and output host's nebula config file
    with open(OUTPUT+hostName+'/'+hostName+'.yml', 'rt') as configFile:
        configData = configFile.read()
        configData = configData.replace(PH_HOST, hostName)
        configData = configData.replace(PH_IP, nebIP)
        configData = configData.replace(PH_LIGHTHOUSE, lightHouse)
        configData = configData.replace(PH_AMLIGHTHOUSE, amLighthouse)
        configFile.close()
    with open(OUTPUT+hostName+'/'+hostName+'.yml', 'wt') as configFile:
        configFile.write(configData)
        configFile.close()

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



if __name__ == "__main__":
    #buildConfig("testbane","199.222.222.222","false","1.1.1.1")
    #buildService("testbane")

    with open(INPUT+'systems.csv', newline='') as systemsCSV:
        systemsContent = csv.reader(systemsCSV)
        # skip header line
        next(systemsContent, None)
        for systemsData in systemsContent:
            print(systemsData[0])
