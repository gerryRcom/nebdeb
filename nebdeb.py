#!/usr/bin/python3
import subprocess
import hashlib


# Set some constants
SYSTEMS = "input/systems.csv"
BINLOCATION = "input/"
BINHASH = "input/binhash"



def generateCert(nebulaIP, fileName):
    certCommand=BINLOCATION+"nebula-cert sign -name "+fileName+" -ip "+nebulaIP
    print(certCommand)
    print(subprocess.call(certCommand, shell=True))

# Get the hash of the nebula binary to comapre against previous run
def getHash():
    with open(BINLOCATION+'nebula', 'rb') as nebulaBinary:
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
        


if __name__ == "__main__":
    compareHash()