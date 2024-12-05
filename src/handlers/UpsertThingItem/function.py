'''Create Thing'''

import json
import os
from dataclasses import asdict, dataclass

import boto3
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.data_classes import event_source, APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_dynamodb import DynamoDBServiceResource
from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_dynamodb.type_defs import PutItemInputTablePutItemTypeDef

from common.model.thing import ThingData, ThingItemKeys, ThingItem, get_keys_from_id
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
class ResponseBody:
    '''Successful API Response body'''
    request_id: str

@dataclass
class ErrorResponseBody():
    '''API error response body'''
    error: str
    message: str


def _upsert_item(item_keys: ThingItemKeys, item_data: ThingData) -> None:
    '''Upsert a Thing in DDB'''
    item = ThingItem(
        **{
            **asdict(item_keys),
            **asdict(item_data)
        }
    )

    ddb_put_item_args: PutItemInputTablePutItemTypeDef = {
        'Item': asdict(item),
        'ConditionExpression': 'attribute_exists(pk) AND attribute_exists(sk)'
    }

    DDB_TABLE.put_item(**ddb_put_item_args)

    return


@LOGGER.inject_lambda_context
@event_source(data_class=APIGatewayProxyEvent)
@lambda_dataclass_response
def handler(event: APIGatewayProxyEvent, context: LambdaContext) -> Output:
    '''Upsert function entry'''
    LOGGER.debug('Event', extra={"message_object": event.raw_event})

    body = event.body or '{}'
    _id = event.path_parameters.get('id', '')
    item_keys = get_keys_from_id(_id)
    item_data = ThingData(
        **json.loads(body),
    )

    if item_data.id == _id:
        _upsert_item(item_keys, item_data)

        response_body = ResponseBody(
            **{
                "request_id": context.aws_request_id
            }
        )
    else:
        response_body = ErrorResponseBody(
            **{
                "error": "BadRequest",
                "message": "Request id does not match payload id"
            }
        )

    output = Output(statusCode=201, body=json.dumps(asdict(response_body)))

    LOGGER.debug('Output', extra={"message_object": asdict(output)})
    return output