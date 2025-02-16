import subprocess
import logging
import re
import sys
import shutil
import hashlib

REGEX_NTAG_CARD_FOUND = re.compile(r'NTAG 2xx')
REGEX_UID_DOUBLE = re.compile(r'(([0-9A-F]{2} ){7})')
REGEX_BLOCK_8_ZEROED = re.compile(r'0x08 \| (0{2} ){4}')

# format loggger so it contains log level and message
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
logging.addLevelName(logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
logging.addLevelName(logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))

# if -v is used in command line, set log level to DEBUG
if '-v' in sys.argv:
    logging.getLogger().setLevel(logging.DEBUG)


def getpwd(uid):
    uid = bytearray.fromhex(uid)
    h = bytearray.fromhex(hashlib.sha1(uid).hexdigest())
    pwd = ""
    pwd += "%02X" % h[h[0] % 20]
    pwd += "%02X" % h[(h[0]+5) % 20]
    pwd += "%02X" % h[(h[0]+13) % 20]
    pwd += "%02X" % h[(h[0]+17) % 20]
    return pwd


def run_pm3_command(command):
    '''Run pm3 command and return output or exit and print error if command fails'''
    try:
        logger.debug("running pm3 command: %s", command)
        pm3_out = subprocess.check_output(['pm3'] + command, stderr=subprocess.STDOUT).decode('utf-8').strip()
        logger.debug("command output:\n%s", pm3_out)
        return pm3_out
    except subprocess.CalledProcessError as e:
        error = e.output.decode('utf-8').strip()
        if 'No port found' in error:
            logger.error('proxmark3 not found, make sure it is connected to your computer')
        else:
            logger.error('pm3 error: %s', error)
        exit(1)
    except FileNotFoundError as e:
        logger.error('pm3 command not found, make sure you have added proxmark3 to your PATH')
        exit(1)
    except Exception as e:
        logger.error('unexpected error: %s', e)
        exit(1)

logger.info("checking if proxmark3 software is installed")
if shutil.which('pm3') is None:
    logger.error("pm3 command not found, make sure you have added proxmark3 to your PATH")
    exit(1)

logger.info("checking if proxmark3 is connected...")
run_pm3_command(['--list'])
logger.info("proxmark3 found")

# scanning for filter tags, we expect "proprietary non iso14443-4 card", "NTAG 2xx" + double UID
logger.info("scanning for filter tags...")
output = run_pm3_command(['-c', 'hf search'])

if not REGEX_NTAG_CARD_FOUND.search(output) or not REGEX_UID_DOUBLE.search(output) or not REGEX_UID_DOUBLE.search(output):
    logger.error("no compatible NTAG found, make sure you have positioned proxmark3 correctly (see README.md)")
    exit(1)

uid = REGEX_UID_DOUBLE.search(output).group(1).replace(' ', '')
logger.info("UID found: %s", uid)

password = getpwd(uid)
logger.info("calculated password: %s", password)

logger.info("setting block 8 to '00 00 00 00'...")
run_pm3_command(['-c', f"hf mfu wrbl -b 8 --data 00000000 -k {password}"])

logger.info("reading block 8 to verify...")
output = run_pm3_command(['-c', f"hf mfu rdbl -b 8 -k {password}"])

if not REGEX_BLOCK_8_ZEROED.search(output):
    logger.error("no compatible NTAG found, make sure you have positioned the HF antenna correctly and you are using compatible filter")
    exit(1)

logger.info("SUCCESS! Filter life has been restored")