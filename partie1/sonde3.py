#!/usr/bin/python3
import subprocess
import signal 
import os
import sys
import time

# on lance un scripte bash qui va recolter des informations concernant la memoire swap
proc = subprocess.Popen(['bash', '-c', '. sonde3_bis.sh; aff'])
# on tue le processus au bout d'une seconde 
time.sleep(1)
proc.kill()