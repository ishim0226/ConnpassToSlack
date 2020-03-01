import os, sys
import requests
import json
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import logging

# param define
logger = logging.getLogger("this")
logger.setLevel(logging.DEBUG)
dynamodb = boto3.resource('dynamodb')
keyword = os.environ['KEYWORD']
url = os.environ['CONNPASS_URL']
table = dynamodb.Table(os.environ['DYNAMO_TABLE'])

# Get the number of target data (results_available) from connpass.
def get_connpass_data_count(url,keyword):
    # param define
    now = datetime.now()
    now_unixtime = int(datetime.timestamp(now))
    # The time goingback from the current time, if the latest updated value of the previously executed process cannot be get.
    init_goingback_time = 86400 # in seconds
    updated_at_init = now_unixtime - init_goingback_time

    try:
        r = requests.get(url, timeout=10,
            params={
                "keyword_or": keyword
                }
            )
        data = json.loads(r.text)
        results_available = int(data["results_available"])
    except Exception as e:
        log_mes = "Failed to get results_available from Connpass. Exception: {}"
        logger.error(log_mes.format(e))
        raise
    else:
        log_mes = "Succeed to get results_available from Connpass. <results_available: {}>"
        logger.debug(log_mes.format(results_available))
        return results_available

# Get the latest updated value of events in dynamodb table.
def get_dynamo_updated_at(table):
    # The latest updated value of the previously executed process is stored in the table as event_id: 0.
    # Therefore, get the lastest updated value from a item with event_id: 0
    try:
        response = table.get_item(
            Key={
                "event_id": 0
            }
        )
        dynamo_updated_at = response['Item']['updated_at']
    except Exception as e:
        # For example, at the first execution after deploying a function.
        # If the item with event_id: 0 cannot be get, return the updated_at_init value instead.
        log_mes = "Failed to get lastest updated_at from Dynamo table failed, so that updated_at will put initial value <{}>. Exception: {}"
        logger.warn(log_mes.format(updated_at_init, e))
        return updated_at_init
    else:
        log_mes = "Succeed to get item from database for latest updated_at. <dynamo_updated_at: {}>"
        logger.debug(log_mes.format(dynamo_updated_at))
        return dynamo_updated_at

# Execute connpass api to get event data.
def get_connpass_data(url,count,start,keyword):
    try:
        r = requests.get(url, timeout=10,
            params={
                "keyword_or": keyword,
                "start": start,
                "count": count,
                "order": 1
                }
            )
        connpass_data = json.loads(r.text)
    except Exception as e:
        log_mes = "Failed to get event data from Connpass. Exception: {}"
        logger.error(log_mes.format(e))
        raise
    else:
        log_mes = "Succeed to get event data from Connpass."
        logger.debug(log_mes.format())
        return connpass_data

# Main process.
# Post event data got from connpass in dynamodb.
def lambda_handler(event, context):
    logger.debug("Process start.")
    
    # Get the total number of events to be searched to get loop_count.
    try:
        results_available = get_connpass_data_count(url,keyword)
        get_count = 15 # Number of events to get at one time.
        start = 1 # Which event of the search results to get.
        loop_count = results_available // get_count + 1 # How many loops are needed.
    except Exception as e:
        # If execution fails, end process.
        log_mes = "Failed to execute get_connpass_data_count. Exception: {}"
        logger.error(log_mes.format(e))
        return
    else:
        log_mes = "Succeed to execute get_connpass_data_count."
        logger.info(log_mes.format())

    # Get latest_update_at from dynamodb.
    try:
        latest_update_at = get_dynamo_updated_at(table)
    except Exception as e:
        # If execution fails, end process.
        log_mes = "Failed to execute get_dynamo_updated_at. Exception: {}"
        logger.error(log_mes.format(e))
        return
    else:
        log_mes = "Succeed to execute get_dynamo_updated_at."
        logger.info(log_mes.format())

    # Loops the required number of times calculated from the total number of searches.
    for i in range(loop_count):
        log_mes = "Loop of 1st depth process started. <loop_count: {}, current_start_grid: {} >"
        logger.debug(log_mes.format(loop_count,start))

        try:
            data = get_connpass_data(url,get_count,start,keyword)
        except Exception as e:
            # If execution fails, end process.
            log_mes = "Failed to execute get_connpass_data. Exception: {}"
            logger.error(log_mes.format(e))
            return
        else:
            log_mes = "Succeed to execute get_connpass_data."
            logger.info(log_mes.format())


        # Loops for the number of events got from connpass.
        count = len(data["events"])
        for i in range(count):
            log_mes = "Loop of 2nd depth process started. <count: {}, processing: {},  event_id: {}>"
            logger.debug(log_mes.format(count, i+1, data["events"][i]["event_id"]))

            # Convert time format to unixtimestamp from isoformat for posting dynamodb.
            dt = datetime.fromisoformat(data["events"][i]["updated_at"])
            updated_at = dt.timestamp()
            updated_at_deci = Decimal(str(updated_at))
            
            # If updated_at_deci_latest is undefined, substitute updated_at_deci of the event,
            # In order to update dynamodb item (event_id: 0) with the latest update value.
            try:
                updated_at_deci_latest
            except:
                updated_at_deci_latest = updated_at_deci
            
            # If the updated value (updated_at) of the event exceeds the latest update value (latest_update_at) of Dynamodb,
            # it is determined that posting to db is necessary.
            if updated_at > latest_update_at :
                log_mes = "Process of posting to db started. <updated_at: {}, event_id: {}, title: {} >"
                logger.debug(log_mes.format(updated_at, data["events"][i]["event_id"], data["events"][i]["title"]))

                # Determine if the event already exists in dynamodb.
                try:
                    response = table.get_item(
                        Key={
                            "event_id": data["events"][i]["event_id"]
                        }
                    )
                    check = response["Item"]["event_id"]

                # If the event does not exist, execute put_item as a new event.
                except:
                    try:
                        table.put_item(
                            Item={
                                "updated_at": updated_at_deci,
                                "event_id": data["events"][i]["event_id"],
                                "title": data["events"][i]["title"],
                                "address": data["events"][i]["address"] or "-",
                                "event_url": data["events"][i]["event_url"],
                                "started_at": data["events"][i]["started_at"]
                            }
                        )
                    # If execution fails, end process.
                    except Exception as e:
                        log_mes = "Failed to insert event data to database. <updated_at: {}, event_id: {}, title: {}> Exception: {}"
                        logger.error(log_mes.format(updated_at, data["events"][i]["event_id"], data["events"][i]["title"], e))
                        return
                    else:
                        log_mes = "Succeed to insert event data to database. <updated_at: {}, event_id: {}, title: {}>"
                        logger.info(log_mes.format(updated_at, data["events"][i]["event_id"], data["events"][i]["title"]))
                
                # If the event exist, execute update_item as a update event.
                else:
                    try:
                        table.update_item(
                            Key={
                                "event_id": data["events"][i]["event_id"]
                            },
                            UpdateExpression="set #u= :u, #t= :t, #a= :a, #e= :e, #s= :s",
                            ExpressionAttributeNames={
                                "#u": "updated_at",
                                "#t": "title",
                                "#a": "address",
                                "#e": "event_url",
                                "#s": "started_at"
                            },
                            ExpressionAttributeValues={
                                ":u": updated_at_deci,
                                ":t": data["events"][i]["title"],
                                ":a": data["events"][i]["address"] or "-",
                                ":e": data["events"][i]["event_url"],
                                ":s": data["events"][i]["started_at"]
                            }
                        )
                    # If execution fails, end process.
                    except Exception as e:
                        log_mes = "Failed to update event data to database. <updated_at: {}, event_id: {}, title: {}> Exception: {}"
                        logger.error(log_mes.format(updated_at, data["events"][i]["event_id"], data["events"][i]["title"], e))
                        return
                    else:
                        log_mes = "Succeed to update event data to database. <updated_at: {}, event_id: {}, title: {}>"
                        logger.info(log_mes.format(updated_at, data["events"][i]["event_id"], data["events"][i]["title"]))
                    
                log_mes = "Process of posting to db ended."
                logger.debug(log_mes.format())

            # If the updated value of the event (updated_at) does not exceed the latest update value of Dynamodb (latest_update_at),
            # it is determined that db posting is unnecessary, and the loop ends.
            else:
                log_mes = "Database update time exceeded connpass update time. <updated_at: {}, event_id: {}, title: {} >"
                logger.debug(log_mes.format(updated_at, data["events"][i]["event_id"], data["events"][i]["title"]))
                
                # Update dynamodb item (event_id: 0) with the latest update value.
                try:
                    table.update_item(
                        Key={
                            "event_id": 0
                        },
                        UpdateExpression="set #u= :u",
                        ExpressionAttributeNames={
                            "#u": "updated_at"
                        },
                        ExpressionAttributeValues={
                            ":u": updated_at_deci_latest
                        }
                    )
                # If execution fails, end process.
                except Exception as e:
                    log_mes = "Failed to updated_at_latest data to database. <updated_at_latest: {}> Exception: {}"
                    logger.error(log_mes.format(updated_at_deci_latest, e))
                    return
                else:
                    log_mes = "Succeed to updated_at_latest data to database. <updated_at_latest: {}>"
                    logger.info(log_mes.format(updated_at_deci_latest))

                logger.debug("Process end.")
                return

            start = start + get_count
            log_mes = "Loop of 2nd depth process ended."
            logger.debug(log_mes.format())

        log_mes = "Loop of 1st depth process ended."
        logger.debug(log_mes.format())


