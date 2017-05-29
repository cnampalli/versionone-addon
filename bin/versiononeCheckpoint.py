import json
import os.path
import splunk.rest

import ConfigParser
from sonarqubeConfiguration import AppConfiguration

#####
# REST endpoint checkpoint, available on /checkpoint (see restmap.conf)
#####
class CheckpointHandler(splunk.rest.BaseRestHandler):

	def __init__(self, method, requestInfo, responseInfo, sessionKey):
		splunk.rest.BaseRestHandler.__init__(self, method, requestInfo, responseInfo, sessionKey)
		input_name='versionone'
		self.checkpoint_file = os.path.join(os.environ["SPLUNK_HOME"], 'var', 'lib', 'splunk', 'modinputs', input_name, 'inputs')

	def writeJson(self, data):
		self.response.setStatus(200)
		self.response.setHeader('content-type', 'application/json')
		self.response.write(json.dumps(data))

	def handle_GET(self):
		checkpointConfig = ConfigParser.RawConfigParser()
		checkpointConfig.read(self.checkpoint_file)
		checkpoint_dic={}
		if checkpointConfig != None:
			for stanza in checkpointConfig.sections():
				checkpoint_dic[stanza] = {}
				for key, val in checkpointConfig.items(stanza):
					if val in [None]:
						val = ''
					checkpoint_dic[stanza][key] = val
		self.writeJson(checkpoint_dic)	


	def handle_POST(self):
		self.response.setStatus(200)

	def handle_DELETE(self):
		if os.path.isfile(str(self.checkpoint_file)) :
			os.remove(self.checkpoint_file)
			self.response.setStatus(200)
		self.response.setStatus(204)
