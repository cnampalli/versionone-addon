#add your custom response handler class to this module
import json, requests, logging
import datetime
import time
import threading

class VersionOne:

    def __init__(self,**args):
        pass

    def __call__(self, response_object,raw_response_output,response_type,req_args,endpoint):
        if response_type == "json":
            logging.info("Response url : %s" %response_object.url)
            output = json.loads(raw_response_output)

            lastId = None
            if  len(output["Assets"]) > 1:
                lastId = output["Assets"][0]["Attributes"]["ChangeDateUTC"]["value"]

            #first response
            for record in output["Assets"]:
                date = record["Attributes"]["ChangeDateUTC"]["value"]
                print_xml_stream_with_time(json.dumps(record), date)

            if not "params" in req_args:
                req_args["params"] = {}

            offset = output["pageStart"]
            page_size = output["pageSize"]
            total = output["total"]
            logging.info("Offset : %s" %offset)
            logging.info("Page Size : %s" %page_size)
            logging.info("Total : %s" %total)

            isLastPage = (( offset + page_size) >= total)
            nextPageStart = offset + page_size
            req_args["params"]["page"] = ("100,%s" % str(nextPageStart))

            #pagination loop
            while not isLastPage:
                next_response = requests.get(endpoint, **req_args)
                output = json.loads(next_response.text)
                #print out results from pagination looping
                for record in output["Assets"]:
                    date = record["Attributes"]["ChangeDateUTC"]["value"]
                    print_xml_stream_with_time(json.dumps(record), date)

                offset = output["pageStart"]
                page_size = output["pageSize"]
                total = output["total"]
                isLastPage = ((offset + page_size) >= total)
                nextPageStart = offset + page_size
                req_args["params"]["page"] = "100," + str(nextPageStart)

            if lastId is not None:
                logging.info("change date utc is given here>>>>>>> %s" %lastId)
                req_args["params"]["filter"] = ("ChangeDateUTC>'%s'" % lastId)

            req_args["params"]["page"] = "100,0"

        else:
            logging.error('Unexpected response type ' % response_type)
            print_xml_stream(raw_response_output)

class VersionOneQuery:

    def __init__(self,**args):
        pass

    def is_last_page(self, jsonOutput):
        return (len(jsonOutput[0])==0)

    def get_most_recent_change_date(self, jsonOutput):
        if  len(jsonOutput[0]) > 0:
            logging.info(" what is the date here>>>> %s " %(jsonOutput[0][0]['ChangeDateUTC']))
            return jsonOutput[0][0]['ChangeDateUTC']
        else:
            return None

    def update_query_arguments(self, jsonOutput, mostRecentChange, req_args):
        payload = json.loads(req_args['data'])
        logging.info('IsLastPage: %s, mostRecentChange:%s' % (self.is_last_page(jsonOutput),mostRecentChange))
        if not self.is_last_page(jsonOutput):   
            # not the last page so update the number of the next page
            pageSize=int(payload['page']['size'])
            pageStart=int(payload['page']['start'])
            newStartAt=pageStart+pageSize
            payload['page']['start']=str(newStartAt)
            logging.info("Going to to retrieve from page %s" % str(newStartAt))
        elif mostRecentChange: 
            # Update the date parameter for next request and reset pagination
            payload['filter']= ["ChangeDateUTC>\'" + str(mostRecentChange) + "\'"]
            payload['page']['start']=0
        else:
            payload['page']['start']=0

        return json.dumps(payload)

    # removed this function at the moment
    def send_events_to_splunk(self, jsonOutput, mostRecentChange):
        for story in jsonOutput[0]:
            date = story["ChangeDateUTC"]
            print_xml_stream_with_time(json.dumps(story), date)


    def __call__(self, response_object,raw_response_output,response_type,req_args,endpoint):
        if response_type == "json":
            logging.info("Response url : %s" %response_object.url)
            output = json.loads(raw_response_output)

            newLastDate = None
            if len(output[0]) > 0:
                newLastDate = output[0][0]['ChangeDateUTC']
                newLastDate = datetime.datetime.strptime(newLastDate[:19], "%Y-%m-%dT%H:%M:%S")
                logging.info("printing last date>> %s" %newLastDate)

            mostRecentChange = self.get_most_recent_change_date(output)

            lastDate = None
            if not "params" in req_args:
                req_args["params"] = {}
            elif "lastDate" in req_args["params"]:
                lastDate = req_args["params"]["lastDate"]
                lastDate = datetime.datetime.strptime(lastDate[:19], "%Y-%m-%d %H:%M:%S")

            try:
                initialPayload = req_args['data']
                logging.info("printing initial pay load >>> %s" %req_args['data'])
                while output:
                    
                    # Performing check for the date to remove duplications
                    for story in output[0]:
                        date = story["ChangeDateUTC"]
                        dateCompare = datetime.datetime.strptime(date[:19], "%Y-%m-%dT%H:%M:%S")
                        if lastDate is not None and (lastDate >= dateCompare):
                            break;
                        else:
                            print_xml_stream_with_time(json.dumps(story), date)


                    #self.send_events_to_splunk(output, mostRecentChange)
                    
                    #Perform a new request after having updated parameters
                    req_args['data'] = self.update_query_arguments(output, mostRecentChange, req_args)
                    
                    logging.info('Next request %s' % req_args['data'])
                    if not self.is_last_page(output):
                        next_response = requests.post(endpoint, **req_args)
                        next_response.raise_for_status()
                        logging.debug("Response of %s: %s" % (next_response.url, next_response.text.replace('\r\n','')))
                        output = json.loads(next_response.text)
                    else:
                        output=None
                    
                newPayload = req_args['data']
                req_args['params']['lastDate'] = newLastDate
                if json.loads(newPayload) == json.loads(initialPayload):
                    req_args["data"] = initialPayload
                        
                logging.info("Checkpoint : %s" % req_args["data"])


            except requests.exceptions.HTTPError,e:
                error_output = next_response.text
                error_http_code = next_response.status_code
                logging.error("HTTP Request error %s while calling %s : %s" % (str(e), next_response.url, next_response.text))
                logging.error("Payload : %s" % (str(req_args["data"])))
                
            except requests.exceptions.Timeout,e:
                logging.error("HTTP Request Timeout error: %s" % str(e))
                
            except Exception as e:
                logging.exception("Exception performing request: %s" % str(e))

        else:
            logging.error('Unexpected response type ' % response_type)
            print_xml_stream(raw_response_output)

#HELPER FUNCTIONS
# prints XML stream
def print_xml_stream(s):
    print "<stream><event unbroken=\"1\"><data>%s</data><done/></event></stream>" % encodeXMLText(s)


def print_xml_stream_with_time(s, date):
    timestamp = time.mktime(datetime.datetime.strptime(date[:-9], "%Y-%m-%dT%H:%M:%S").timetuple())
    print "<stream><event unbroken=\"1\"><time>%s</time><data>%s</data><done/></event></stream>" % (
        encodeXMLText(str(timestamp)), encodeXMLText(s))


def encodeXMLText(text):
    text = text.replace("&", "&amp;")
    text = text.replace("\"", "&quot;")
    text = text.replace("'", "&apos;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace("\n", "")
    return text
    
