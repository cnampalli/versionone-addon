import ConfigParser
import os.path
from abc import ABCMeta, abstractmethod
import sys

#############
# Class used to create inputs.conf file
#############

class AbstractAppConfiguration:
  __metaclass__ = ABCMeta

  def __init__(self, app_dir=None):
    if not app_dir:
      app_name = __file__.split(os.sep)[-3]
      app_dir = os.path.join(os.environ["SPLUNK_HOME"], 'etc', 'apps', app_name)
    self.configInputsFile = os.path.join(app_dir, 'default', 'inputs.conf')
    self.configFile = os.path.join(app_dir, 'config.properties')

  def addParameters(self, inputConfig, inputSection, outputConfig, outputSection, parameters):
    """ Adds a parameters to a config file using an input config, add a hashmap containg default values if the value is missing in the input
        inputConfig -- ConfigParser to read the value from
        inputSection -- Name of the input section to read the value from
        outputConfig -- Output configuration object
        outputSection -- Section of the outputConfig in which to write the parameter
        parameters -- Hashmap containing default values
    """
    for parameter in parameters:
      if inputConfig.has_option(inputSection, parameter):
        parameterValue = inputConfig.get(inputSection, parameter)
        outputConfig.set(outputSection, parameter, parameterValue)
      elif parameters[parameter]:
        parameterValue = parameters[parameter]
        outputConfig.set(outputSection, parameter, parameterValue)
      else:
        print "WARN: parameter {0} is missing in section {1}".format(parameter, outputSection)  

  def addAuthenticationConfiguration(self, inputConfig, inputSection, outputConfig, outputSection):
    """ Adds specific authentication parameters
    """
    auth_type = inputConfig.get(inputSection, 'auth_type')
    outputConfig.set(outputSection, 'auth_type', auth_type)
    parameters ={
      'none'   : [],
      'basic'  : ['auth_user', 'auth_password'],
      'digest' : ['auth_user', 'auth_password'],
      'oauth1' : ['oauth1_client_key', 'oauth1_client_secret', 'oauth1_access_token', 'oauth1_access_token_secret'],
      'oauth2' : ['oauth2_token_type', 'oauth2_access_token', 'oauth2_refresh_token', 'oauth2_refresh_url', 'oauth2_refresh_props', 'oauth2_client_id', 'oauth2_client_secret' ],
      'custom' : ['custom_auth_handler_args']
    }[auth_type]
    self.addParameters (inputConfig, inputSection, outputConfig, outputSection, parameters)

  @abstractmethod
  def handleSection():
    pass

  def createInputsConfiguration(self, configPath=None, fileWriteMode='w'):
    """Creates or appends to the existing configuration file
    """
    if not configPath:
      configPath = self.configFile
    if os.path.isfile(str(configPath)) :
      inputConfig = ConfigParser.RawConfigParser()
      inputConfig.read(configPath)
      with open(self.configInputsFile, fileWriteMode) as configInputsFile:
        outputConfig = ConfigParser.RawConfigParser()
        for inputSection in inputConfig.sections():
          self.handleSection(inputConfig, inputSection, outputConfig)
        outputConfig.write(configInputsFile)
    else:
      print ('%s is not  a correct input file' % configPath)


  def appendToInputConfiguration(self, inputConfig):
    """Creates or appends to the existing configuration file
    """
    with open(self.configInputsFile, 'a') as configInputsFile:
      outputConfig = ConfigParser.RawConfigParser()
      for inputSection in inputConfig.sections():
        self.handleSection(inputConfig, inputSection, outputConfig)
      outputConfig.write(configInputsFile)

  def readConfig(self):
    if os.path.isfile(str(self.configFile)) :
      config = ConfigParser.RawConfigParser()
      config.read(self.configFile)
      return config
    else:
      print ('%s is not  a correct input file' % self.configFile)

  def writeConfig(self, config):
    with open(self.configFile, 'w') as configFile:
      config.write(configFile)
####
# Specific VersionOne
####
class AppConfiguration(AbstractAppConfiguration):
  def __init__(self, app_dir=None):
    super(AppConfiguration, self).__init__(app_dir)
    self.section = 'versionone://{host}-{project}'
    self.endpoint_query = '{protocol}://{host}/{project}/query.legacy.v1'
    self.default_configuration_query = {
        'auth_type' : 'custom',
        'custom_auth_handler' : 'VersionAccessTokenHandler',
        'http_method': 'POST',
        'index_error_response_codes': '0',
        'response_type': 'json',
        'sequential_mode' : '0',
        'sourcetype': 'versiononequery_api',
        'streaming_request' : '0',
        'index' : 'aaam_devops_versionone_idx',
        'disabled' : '0',
        'response_handler' : 'VersionOneQuery',
        'interval' : '300', 
        'delimiter' : ';',
        'request_payload' : '{"from": "Story", "select": [ "Name", "Estimate", "DetailEstimate", "CreateDateUTC", "ChangedBy", "CreatedBy", "ClosedDateUTC", "ClosedBy", "ChangeDateUTC", "Scope", "Status", "ID", "Number", "Description", "Team", "Timebox", "Inactive", "ToDo", "AssetState", "OriginalEstimate", "Source", "Risk", "Customer", "Category", "Actuals", "Links","AffectedByDefects","IdentifiedIn","ChangeSets","Goals","Dependencies","Dependants", "Key","Parent","BudgetAllocation"], "page" :{ "start": "0", "size": "50"}, "filter": [ "ChangeDateUTC>\'1970-01-01T00:00:00.0000000Z\'" ], "sort": ["-ChangeDateUTC"]}',
        'http_header_propertys' : 'Accept=application/json'
    }

    self.endpoint_data = {
        'auth_type' : 'custom',
        'custom_auth_handler': 'VersionAccessTokenHandler',
        'http_method': 'GET',
        'index_error_response_codes': '0',
        'response_type': 'json',
        'sequential_mode' : '0',
        'sourcetype' : 'versionone_api',
        'streaming_request' : '0',
        'index' : 'aaam_devops_versionone_idx',
        'disabled' : '0',
        'response_handler': 'VersionOne',
        'interval' : '300', 
        'delimiter' : ';',
        'url_args': 'sel=Name,Estimate,DetailEstimate,CreateDateUTC,ChangedBy,CreatedBy,ClosedDateUTC,ClosedBy,ChangeDateUTC,Scope,Status,ID,Number,Description,Team,Timebox,Inactive,ToDo,AssetState,OriginalEstimate,Source,Risk,Customer,Category,Actuals,Links,AffectedByDefects,IdentifiedIn,ChangeSets,Goals,Dependencies,Dependants,Key,Parent,BudgetAllocation;page=100,0;sort=-ChangeDateUTC',
        'http_header_propertys'  : 'Accept=application/json'}
    self.default_configuration_data = '{protocol}://{host}/{project}/rest-1.v1/Data/Story'
    
    #Lookup table parameters    
    self.lookup_section = 'versiononeLookups://lookup-{host}-{project}'
    self.lookup_params = {
      'custom_auth_handler': 'VersionAccessTokenHandler',
      'interval': '300',
      'tables': '{"from": "Epic", "select": ["Name"], "page" : {"start": 0, "size": 100}}; {"from": "StoryCategory", "select": ["Name"], "page" : {"start": 0, "size": 100}}; {"from": "StoryStatus", "select": ["Name"], "page" : {"start": 0, "size": 100}}; {"from": "Timebox", "select": ["Name",  "EndDate", "BeginDate", "Workitems.ToDo.@Sum"], "page" : {"start": 0, "size": 100}}; {"from": "Theme", "select": ["Name"], "page" : {"start": 0, "size": 100}}; {"from": "WorkitemRisk", "select": ["Name"], "page" : {"start": 0, "size": 100}}; {"from": "Scope", "select": ["Name"], "page" : {"start": 0, "size": 100}}; {"from": "StorySource", "select": ["Name"], "page" : {"start": 0, "size": 100}}; {"from": "Team", "select": ["Name"], "page" : {"start": 0, "size": 100}}'
    }


  def handleSection(self, inputConfig, inputSection, outputConfig):
    host = inputConfig.get(inputSection, 'host')
    protocol = inputConfig.get(inputSection, 'protocol')
    project = inputConfig.get(inputSection, 'project')
    access_token = inputConfig.get(inputSection, 'access_token')
    inputConfig.set(inputSection, 'custom_auth_handler_args', 'access_token=%s' % access_token)
    
    section = self.section.format(host=host.replace('/', '-'), project=project)
    outputConfig.add_section(section)
    if inputConfig.get(inputSection, 'response_handler') == 'VersionOneQuery':
      outputConfig.set(section, 'endpoint', self.endpoint_query.format(protocol=protocol, host=host, project=project))
      self.addAuthenticationConfiguration(inputConfig, inputSection, outputConfig, section)
      self.addParameters(inputConfig, inputSection, outputConfig, section, self.default_configuration_query)

    elif inputConfig.get(inputSection, 'response_handler') == 'VersionOne':
      outputConfig.set(section, 'endpoint', self.default_configuration_data.format(protocol=protocol, host=host, project=project))
      self.addAuthenticationConfiguration(inputConfig, inputSection, outputConfig, section)
      self.addParameters(inputConfig, inputSection, outputConfig, section, self.endpoint_data)
    else:
      print("Unkown response handler %s " % inputConfig.get(inputSection, 'response_handler'))  

    # Create lookups input
    lookupSection = self.lookup_section.format(host=host.replace('/', '-'), project=project)
    outputConfig.add_section(lookupSection)
    outputConfig.set(lookupSection, 'endpoint', self.endpoint_query.format(protocol=protocol, host=host, project=project))
    self.addAuthenticationConfiguration(inputConfig, inputSection, outputConfig, lookupSection)    
    self.addParameters(inputConfig, inputSection, outputConfig, lookupSection, self.lookup_params)