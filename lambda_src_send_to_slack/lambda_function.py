import os, sys
#sys.path.append(os.path.join(os.path.dirname(__file__), 'site-packages'))
#import warnings
#warnings.simplefilter('ignore')
import requests
import json
from boto3.dynamodb.types import TypeDeserializer
import logging

# param define
logger = logging.getLogger("this")
logger.setLevel(logging.DEBUG)
deserializer = TypeDeserializer()
webhook_url = os.environ['WEBHOOK_URL']

try:
    update_notify = os.environ['UPDATE_NOTIFY']
except:
    update_notify = False

# Check whether the address of the received dynamo stream event matches the address of the environment variable.
def address_check(address_filter_str,address):
    address_filter_list = address_filter_str.split(',')
    match_count = 0
    for i in address_filter_list:
        if i in address:
            match_count += 1
    return match_count

# Convert dynamo stream event record to dict.
def deserialize(record):
    d = {}
    for key in record:
        d[key] = deserializer.deserialize(record[key])
    return d

# Main process.
# Post the event received from dynamo stream to slack.
def lambda_handler(event, context):
    logger.debug("Process start.")

    # Extract item information from event received from dynamo stream.
    try:
        record = event['Records'][0]['dynamodb']['NewImage']
        item = deserialize(record)
    # If execution fails, end process.
    except Exception as e:
        log_mes = "Failed to extraction event data to database. <DynamoRecords: {}> Exception: {}"
        logger.error(log_mes.format(event['Records'][0], e))
        return

    # If event_id is 0,
    # it skips posting because it is a record for managing the latest updated value.
    if item["event_id"] == 0:
        log_mes = "Skiped to post, because this is reserved event_id. <event_id: {}>"
        logger.debug(log_mes.format(item["event_id"]))
        return
        
    # Format started_at.
    started_at_str = item["started_at"]
    started_at_str = started_at_str.replace("T", " ")
    started_at_str = started_at_str.replace("+09:00", "")

    # Define contents to be posted to slack.
    value_text = (item["event_url"] + '\n' + 
        "Address: " + item["address"] + '\n' + 
        "Started at: " + started_at_str)

    # Determine if the event is new or updated and define a title to post to slack.
    eventName = event['Records'][0]['eventName']
    if eventName == "INSERT" :
        pretext = '[New] Connpass Study Session Information.'
        color = "#4169E1"
    elif eventName == "MODIFY" :

        # When update_notify is false, it does not notify update information.
        if not update_notify :
            log_mes = "This event didn't post to slack due to update notification. <title: {}>"
            logger.debug(log_mes.format(item["title"]))
            return
        pretext = '[Update] Connpass Study Session Information.'
        color = "#D3D3D3"
    else:
        log_mes = "Unexpected eventName. <eventName: {}>"
        logger.error(log_mes.format(eventName))
        return

    # Check the address and post it to slack only if it matches the address of the event.
    address_count = address_check(os.environ['ADDRESS_FILTER'],item["address"])
    if address_count > 0:
        try:
            requests.post(webhook_url, data = json.dumps({
                "attachments":[
                    {
                        "fallback": item["title"],
                        "pretext": pretext,
                        "color": color,
                        "fields":[
                        {
                            "title": item["title"],
                            "value": value_text
                        }
                        ]
                    }
                ]
            }))
        # If execution fails, end process.
        except Exception as e:
            log_mes = "Failed to post event data to slack. Exception: {}"
            logger.error(log_mes.format(e))
            return
        else:
            log_mes = "Succeed to posted to slack. <title: {}>"
            logger.info(log_mes.format(item["title"]))

    logger.debug("process end.")
    return
