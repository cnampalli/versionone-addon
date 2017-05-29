"""
VersionOne lookup getter
"""
import sys
import json
import requests
from lookupfiles import get_temporary_lookup_file
from lookupfiles import get_lookup_table_location
from lookupfiles import update_lookup_table
import logging
from time import sleep
import xml.dom.minidom

#set up logging
logging.root
logging.root.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s %(message)s')
#with zero args , should go to STD ERR
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.root.addHandler(handler)

##############
# MODULAR INPUT SCHEME
##############
SCHEME = """<scheme>
    <title>VersionOneLookups</title>
    <description>VersionOneLookups input for polling data from VersionOne to setup lookup tables</description>
    <use_external_validation>true</use_external_validation>
    <streaming_mode>simple</streaming_mode>
    <use_single_instance>true</use_single_instance>

    <endpoint>
        <args>    
            <arg name="name">
                <title>VersionOneLookup input name</title>
                <description>Name of this VersionOneLookup input</description>
            </arg>            
            <arg name="endpoint">
                <title>Endpoint URL</title>
                <description>URL to send the HTTP GET request to</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>true</required_on_create>
            </arg>
            <arg name="http_method">
                <title>HTTP Method</title>
                <description>HTTP method to use.Defaults to GET. POST and PUT are not really RESTful for requesting data from the API, but useful to have the option for target APIs that are "REST like"</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="request_payload">
                <title>Request Payload</title>
                <description>Request payload for POST and PUT HTTP Methods</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="auth_type">
                <title>Authentication Type</title>
                <description>Authentication method to use : none | basic | digest | oauth1 | oauth2 | custom</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>true</required_on_create>
            </arg>
            <arg name="auth_user">
                <title>Authentication User</title>
                <description>Authentication user for BASIC or DIGEST auth</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="auth_password">
                <title>Authentication Password</title>
                <description>Authentication password for BASIC or DIGEST auth</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="custom_auth_handler">
                <title>Custom_Auth Handler</title>
                <description>Python classname of custom auth handler</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="custom_auth_handler_args">
                <title>Custom_Auth Handler Arguments</title>
                <description>Custom Authentication Handler arguments string ,  key=value,key2=value2</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="delimiter">
                <title>Delimiter</title>
                <description>Delimiter to use for any multi "key=value" field inputs</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="tables">
                <title>Tables</title>
                <description>Tables to query</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>          
            <arg name="request_timeout">
                <title>Request Timeout</title>
                <description>Request Timeout in seconds</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
        </args>
    </endpoint>
</scheme>
"""

def do_scheme():
    print SCHEME

##############
# MODULAR INPUT VALIDATION
##############

def do_validate():
    try:
        config = get_validation_config() 
    except:
        logging.exception("Error while loading versiononeLookups configuration")

def get_validation_config():
    val_data = {}

    # read everything from stdin
    val_str = sys.stdin.read()

    # parse the validation XML
    doc = xml.dom.minidom.parseString(val_str)
    root = doc.documentElement

    logging.debug("XML: found items")
    item_node = root.getElementsByTagName("item")[0]
    if item_node:
        logging.debug("XML: found item")

        name = item_node.getAttribute("name")
        val_data["stanza"] = name

        params_node = item_node.getElementsByTagName("param")
        for param in params_node:
            name = param.getAttribute("name")
            logging.debug("Found param %s" % name)
            if name and param.firstChild and \
               param.firstChild.nodeType == param.firstChild.TEXT_NODE:
                val_data[name] = param.firstChild.data

    return val_data

def usage():
    print "usage: %s [--scheme|--validate-arguments]"
    logging.error("Incorrect Program Usage")
    sys.exit(2)

#read XML configuration passed from splunkd, need to refactor to support single instance mode
def get_input_config():
    config = {}

    try:
        # read everything from stdin
        config_str = sys.stdin.read()

        # parse the config XML
        doc = xml.dom.minidom.parseString(config_str)
        root = doc.documentElement
        
        session_key_node = root.getElementsByTagName("session_key")[0]
        if session_key_node and session_key_node.firstChild and session_key_node.firstChild.nodeType == session_key_node.firstChild.TEXT_NODE:
            data = session_key_node.firstChild.data
            config["session_key"] = data 
            
        server_uri_node = root.getElementsByTagName("server_uri")[0]
        if server_uri_node and server_uri_node.firstChild and server_uri_node.firstChild.nodeType == server_uri_node.firstChild.TEXT_NODE:
            data = server_uri_node.firstChild.data
            config["server_uri"] = data   
            
        conf_node = root.getElementsByTagName("configuration")[0]
        if conf_node:
            logging.debug("XML: found configuration")
            stanza = conf_node.getElementsByTagName("stanza")[0]
            if stanza:
                stanza_name = stanza.getAttribute("name")
                if stanza_name:
                    logging.debug("XML: found stanza " + stanza_name)
                    config["name"] = stanza_name

                    params = stanza.getElementsByTagName("param")
                    for param in params:
                        param_name = param.getAttribute("name")
                        logging.debug("XML: found param '%s'" % param_name)
                        if param_name and param.firstChild and \
                           param.firstChild.nodeType == param.firstChild.TEXT_NODE:
                            data = param.firstChild.data
                            config[param_name] = data
                            logging.debug("XML: '%s' -> '%s'" % (param_name, data))

        checkpnt_node = root.getElementsByTagName("checkpoint_dir")[0]
        if checkpnt_node and checkpnt_node.firstChild and \
           checkpnt_node.firstChild.nodeType == checkpnt_node.firstChild.TEXT_NODE:
            config["checkpoint_dir"] = checkpnt_node.firstChild.data

        if not config:
            raise Exception, "Invalid configuration received from Splunk."

        
    except Exception, e:
        logging.exception("Error occured while getting Splunk configuration %s" % str(e))
        raise Exception, "Error getting Splunk configuration via STDIN: %s" % str(e)

    return config

def do_run():
    session = requests.Session()

    config = get_input_config()
    token = config.get("access_token")
    SESSION_TOKEN = config.get("session_key")

    # Connection variables
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Accept": "application/json"
    }
    tables = config.get("tables")
    query_url =  config.get("endpoint")
    
    logging.info("Tables to query : %s" % tables)
    if tables != None:
        for query in tables.split(';'):
            query_json=json.loads(query)
            table = query_json['from']
            logging.info("Sending query for table : %s" % table)

            try:
                custom_auth_handler=config.get("custom_auth_handler")
                auth = None
                delimiter=config.get("delimiter",",")
                if custom_auth_handler:
                    module = __import__("authhandlers")
                    class_ = getattr(module,custom_auth_handler)
                    custom_auth_handler_args={}
                    custom_auth_handler_args_str=config.get("custom_auth_handler_args")
                    if not custom_auth_handler_args_str is None:
                        custom_auth_handler_args = dict((k.strip(), v.strip()) for k,v in (item.split('=',1) for item in custom_auth_handler_args_str.split(delimiter)))
                    auth = class_(**custom_auth_handler_args)
                r = session.get(url=query_url, headers=headers, data=query, auth=auth)
                r.raise_for_status()
                matches = r.json()[0]
                logging.debug("Matches : %s" % matches)

                # Clear lookup file
                lookup_file = get_temporary_lookup_file(table)
                select_query=query_json['select']
                lookup_file.write('"oid", "' + '", "'.join(select_query) + '"\n')
                
                while len(matches)>0:
                    for match in matches:
                        attributes = [match['_oid']]
                        for attribute in select_query:
                            attributes.append(match[str(attribute)])
                        logging.info(attributes)
                        lookup_file.write('"'+ '", "'.join(str(item) for item in attributes) + '"\n')

                    # GET Next page
                    query_json['page']['start'] = query_json['page']['start'] + 1
                    logging.info('Getting page %s', query_json['page']['start'])
                    r = session.get(url=query_url, headers=headers, data=json.dumps(query_json), auth=auth)
                    r.raise_for_status()
                    matches = r.json()[0]

                lookup_file.flush()
                
                # Update existing lookup csv file
                success = update_lookup_table(lookup_file.name, 'versionone_' + table + '.csv', 'aaam-devops-versionone-addon', "nobody", SESSION_TOKEN)
             
            except requests.exceptions.HTTPError,e:
                error_output = r.text
                error_http_code = r.status_code            
                logging.exception("HTTP Request error: %s" % str(e))
                continue
            except requests.exceptions.Timeout,e:
                logging.exception("HTTP Request Timeout error: %s" % str(e))
                continue
            except Exception as e:
                logging.exception("Exception performing request: %s" % str(e))
                continue

##############
# MAIN
##############
if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == "--scheme":
            do_scheme()
        elif sys.argv[1] == "--validate-arguments":
            do_validate()
        else:
            usage()
    else:
        logging.info("Running version one lookup update script")
        try:
            do_run()
        except:
            logging.exception("An error occured while updating lookups")
    sys.exit(0)