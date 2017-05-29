#!/usr/bin/env python
import sys
sys.path.insert(0, 'bin')
from versiononeConfiguration import AppConfiguration

def help():
  print """
%s <filename>
Generates the configuration files for the versionone splunk plugin using the input config.conf file
Options are :
 - help : print this help
""" % sys.argv[0]

if __name__ == '__main__':

  if len(sys.argv)!=2 or sys.argv[1]=='help':
    help()
    exit(0)
  configPath=sys.argv[1]
  
  configuration = AppConfiguration('./')
  configuration.createInputsConfiguration(configPath)