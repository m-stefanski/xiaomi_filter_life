import sys
import hashlib

def getpwd(uid):
    uid = bytearray.fromhex(uid)
    h = bytearray.fromhex(hashlib.sha1(uid).hexdigest())
    pwd = ""
    pwd += "%02X" % h[h[0] % 20]
    pwd += "%02X" % h[(h[0]+5) % 20]
    pwd += "%02X" % h[(h[0]+13) % 20]
    pwd += "%02X" % h[(h[0]+17) % 20]
    return pwd

print("PWD:", getpwd(sys.argv[1]))