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

from common.model.thing import ThingData, ThingItemKeys, ThingItem, create_keys, get_id_from_keys
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
    '''Creation API Response body'''
    id: str


def _create_item(item_data: ThingData) -> str:
    '''Create a Thing in DDB'''
    item_keys = create_keys()
    item_data.id = get_id_from_keys(item_keys)

    item = ThingItem(
        **{
            **asdict(item_keys),
            **asdict(item_data)
        }
    )

    ddb_put_item_args: PutItemInputTablePutItemTypeDef = {
        'Item': asdict(item),
        'ConditionExpression': 'attribute_not_exists(pk) AND attribute_not_exists(sk)'
    }

    DDB_TABLE.put_item(**ddb_put_item_args)

    return item_data.id


@LOGGER.inject_lambda_context
@event_source(data_class=APIGatewayProxyEvent)
@lambda_dataclass_response
def handler(event: APIGatewayProxyEvent, context: LambdaContext) -> Output:
    '''Create function entry'''
    LOGGER.debug('Event', extra={"message_object": event.raw_event})

    body = event.body or '{}'
    item_data = ThingData(**json.loads(body))
    _id = _create_item(item_data)

    response_body = ResponseBody(
        **{
            "id": _id
        }
    )

    output = Output(statusCode=201, body=json.dumps(asdict(response_body)))

    LOGGER.debug('Output', extra={"message_object": asdict(output)})
    return output
