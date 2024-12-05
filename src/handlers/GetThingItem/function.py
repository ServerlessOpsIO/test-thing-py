'''Get Thing'''

import json
import os
from dataclasses import asdict, dataclass

import boto3
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.data_classes import event_source, APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_dynamodb import DynamoDBServiceResource
from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_dynamodb.type_defs import GetItemInputTableGetItemTypeDef

from common.model.thing import ThingData, ThingItem, ThingItemKeys, get_keys_from_id
from common.util.dataclasses import lambda_dataclass_response

LOGGER = Logger(utc=True)

DDB: DynamoDBServiceResource = boto3.resource('dynamodb', 'us-east-1')
DDB_TABLE: Table = DDB.Table(os.environ.get('DDB_TABLE_NAME', ''))

@dataclass
class Output:
    '''Function response'''
    statusCode: int
    body: str

@dataclass
class ResponseBody(ThingData):
    '''API Response body'''

@dataclass
class ErrorResponseBody():
    '''API error response body'''
    error: str
    message: str


def _get_item(item_keys: ThingItemKeys) -> ThingData | None:
    '''Get a Thing in DDB'''
    ddb_get_item_args: GetItemInputTableGetItemTypeDef = {
        'Key': {
            **asdict(item_keys)
        }
    }

    get_item_response = DDB_TABLE.get_item(**ddb_get_item_args)
    if 'Item' in get_item_response:
        item = ThingItem(**get_item_response.get('Item', {}))
        data = ThingData(**item.get_data())
    else:
        data = None
    return data


@LOGGER.inject_lambda_context
@event_source(data_class=APIGatewayProxyEvent)
@lambda_dataclass_response
def handler(event: APIGatewayProxyEvent, context: LambdaContext) -> Output:
    '''Function entry'''
    LOGGER.info('Event', extra={"message_object": event.raw_event})

    item_keys = get_keys_from_id(event.path_parameters.get('id', ''))
    data = _get_item(item_keys)

    if data is None:
        error = ErrorResponseBody(
            **{
                "error": "ThingNotfound",
                "message": "Thing not found"
            }
        )
        output = Output(statusCode=404, body=json.dumps(asdict(error)))
    else:
        output = Output(statusCode=200, body=json.dumps(asdict(data)))

    LOGGER.debug('Output', extra={"message_object": asdict(output)})
    return output