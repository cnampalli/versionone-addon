import json
import splunk.rest

import ConfigParser
from versiononeConfiguration import AppConfiguration

#####
# REST endpoint setup, available on /setup (see restmap.conf)
#####
class SetupHandler(splunk.rest.BaseRestHandler):

	def __init__(self, method, requestInfo, responseInfo, sessionKey):
		splunk.rest.BaseRestHandler.__init__(self,
			method, requestInfo, responseInfo, sessionKey)
		self.configuration = AppConfiguration()

	def writeJson(self, data):
		self.response.setStatus(200)
		self.response.setHeader('content-type', 'application/json')
		self.response.write(json.dumps(data))

	def handle_GET(self):
		confDict = self.configuration.readConfig()
		confInfo = {}
		if confDict != None:
			for stanza in confDict.sections():
				confInfo[stanza] = {}
				for key, val in confDict.items(stanza):
					if val in [None]:
						val = ''
					confInfo[stanza][key] = val
		self.writeJson(confInfo)

	def handle_POST(self):
		all_settings = json.loads(self.request["payload"])
		config = ConfigParser.RawConfigParser()
		for stanza in all_settings :
			config.add_section(stanza)
			settings = all_settings[stanza]
			for key in settings :
				config.set(stanza, key, settings[key])
		
		self.configuration.writeConfig(config)
		self.configuration.createInputsConfiguration()