'''Delete ThingItem'''

import json
import os
from dataclasses import asdict, dataclass

import boto3
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.data_classes import event_source, APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_dynamodb import DynamoDBServiceResource
from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_dynamodb.type_defs import DeleteItemInputTableDeleteItemTypeDef

from common.model.thing import ThingItemKeys, get_keys_from_id
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
    '''API Response body'''
    request_id: str


def _delete_item(item_keys: ThingItemKeys) -> None:
    '''delete a Thing in DDB'''
    ddb_args: DeleteItemInputTableDeleteItemTypeDef = {
        'Key': {
            **asdict(item_keys)
        },
        'ConditionExpression': 'attribute_exists(pk) AND attribute_exists(sk)'
    }

    DDB_TABLE.delete_item(**ddb_args)
    return


@LOGGER.inject_lambda_context
@event_source(data_class=APIGatewayProxyEvent)
@lambda_dataclass_response
def handler(event: APIGatewayProxyEvent, context: LambdaContext) -> Output:
    '''Function entry'''
    LOGGER.info('Event', extra={"message_object": event.raw_event})

    item_keys = get_keys_from_id(event.path_parameters.get('id', ''))
    _delete_item(item_keys)

    response_body = ResponseBody(
        **{
            "request_id": context.aws_request_id
        }
    )

    output = Output(statusCode=200, body=json.dumps(asdict(response_body)))

    LOGGER.debug('Output', extra={"message_object": asdict(output)})
    return output