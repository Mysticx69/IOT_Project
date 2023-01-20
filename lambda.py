"""Lambda to handle API requests"""
import json
import logging

import boto3

from custom_encoder import CustomEncoder

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLENAME = 'api-db'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLENAME)


def lambda_handler(event, context):
    logger.info(event)
    http_method = event['httpMethod']
    path = event['path']
    if http_method == 'GET' and path == '/health':
        response = build_response(200, {'Message': 'API is working and healthy!'})
    elif http_method == 'GET' and path == '/capteur':
        response = get_capteur(event['queryStringParameters']['id'])
    elif http_method == 'GET' and path == '/capteurs':
        response = get_capteurs()
    elif http_method == 'POST' and path == '/capteur':
        response = save_capteur(json.loads(event['body']))
    elif http_method == 'DELETE' and path == '/capteur':
        requestbody = json.loads(event['body'])
        response = delete_capteur(requestbody['id'])
    elif http_method == 'DELETE' and path == '/capteurs':
        response = delete_capteurs()

    else:
        response = build_response(404, 'Not Found')

    return response


def get_capteur(id):
    try:
        response = table.get_item(Key={'id': id})
        if 'Item' in response:
            return build_response(200, response['Item'])

        return build_response(404, {'Message': f'id: {id} not found'})

    except Exception as ex:
        logger.exception(
            'Resource ou methode non disponible, vérifiez votre request. ErrorCode:  %s:', ex)


def get_capteurs():
    try:
        response = table.scan()
        result = response['Items']

        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            result.extend(response['Items'])

        body = {'capteurs': response}

        return build_response(200, body)

    except Exception as ex:
        logger.exception(
            'Resource ou methode non disponible, vérifiez votre request. ErrorCode:  %s:', ex)


def save_capteur(requestbody):
    try:
        table.put_item(Item=requestbody)

        body = {
            'Operation': 'Register Sensors informations',
            'Status': 'SUCCESS',
            'Item': requestbody
        }
        if requestbody["valueFeu"] == "1":
            send_sms(requestbody["CapteurPosX"],requestbody["CapteurPosY"],requestbody["NumLabo"],"feu")
        elif requestbody["etatCO2"] == "ALERTE CO2":
            send_sms(requestbody["CapteurPosX"],requestbody["CapteurPosY"],requestbody["NumLabo"],"co2")
        return build_response(200, body)

    except Exception as ex:
        logger.exception(
            'Resource ou methode non disponible, vérifiez votre request. ErrorCode:  %s:', ex)


def delete_capteur(id):
    try:
        response = table.delete_item(Key={'id': id}, ReturnValues='ALL_OLD')
        body = {'Operation': 'Delete Sensors informations', 'Status': 'SUCCESS', 'Item': response}

        return build_response(200, body)

    except Exception as ex:
        logger.exception(
            'Resource ou methode non disponible, vérifiez votre request. ErrorCode:  %s:', ex)


def delete_capteurs():
    try:
        scan = table.scan()
        with table.batch_writer() as batch:
            for each in scan['Items']:
                batch.delete_item(
                    Key={
                        'id': each['id']
                    }
                )

        body = {
                'Message' : 'Deleted all items successfully'
            }

        return build_response(200, body)
    
    except Exception as ex:
        logger.exception(
            'Resource ou methode non disponible, vérifiez votre request. ErrorCode:  %s:', ex)    
       
def send_sms(posX,posY,NumLabo,type):
    # Create SNS client
    sns = boto3.client('sns')

    # Define SMS parameters
    topic_arn = "arn:aws:sns:us-east-1:206009336603:notification"
    if type == "feu":
        message = f"!!Alerte!! Feu detecté sur le capteur X! \nLat,Long: ({posX},{posY}) \nNuméro de labo: {NumLabo}"
    elif type =="co2":
        message = f"!!Alerte!! Taux de CO2 anormalement élevé détecté par le capteur X! \nLat,Long: ({posX},{posY}) \nNuméro de labo: {NumLabo}"
    sns.set_sms_attributes(
        attributes={
            'DefaultSMSType': 'Transactional',
            'DeliveryStatusSuccessSamplingRate': '100',
            'DefaultSenderID': 'IotCpe'
        }
    )
    # Send SMS
    response = sns.publish(
        TopicArn=topic_arn,
        Message=message
    )
           

    # Return the response
    return response

def build_response(statusCode, body=None):
    response = {
        'statusCode': statusCode,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }

    if body is not None:
        response['body'] = json.dumps(body, cls=CustomEncoder)

    return response
