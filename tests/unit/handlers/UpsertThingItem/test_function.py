'''Test UpsertThingItem'''

from dataclasses import asdict
import json
import jsonschema
import os
from types import ModuleType
from typing import cast, Generator, Tuple

import pytest
from pytest_mock import MockerFixture

import boto3
from moto import mock_aws
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

from common.model.thing import ThingData, ThingItemKeys, get_keys_from_id
from common.test.aws import create_lambda_function_context

from src.handlers.UpsertThingItem.function import Output, ResponseBody

FN_NAME = 'UpsertThingItem'
DATA_DIR = './data'
FUNC_DATA_DIR = os.path.join(DATA_DIR, 'handlers', FN_NAME)
EVENT = os.path.join(FUNC_DATA_DIR, 'event.json')
EVENT_SCHEMA = os.path.join(FUNC_DATA_DIR, 'event.schema.json')
DATA = os.path.join(FUNC_DATA_DIR, 'data.json')
DATA_SCHEMA = os.path.join(FUNC_DATA_DIR, 'data.schema.json')
OUTPUT = os.path.join(FUNC_DATA_DIR, 'output.json')
OUTPUT_SCHEMA = os.path.join(FUNC_DATA_DIR, 'output.schema.json')
RESPONSE = os.path.join(FUNC_DATA_DIR, 'response.json')
RESPONSE_SCHEMA = os.path.join(FUNC_DATA_DIR, 'response.schema.json')


### Fixtures
@pytest.fixture()
def mock_context(function_name=FN_NAME):
    '''context object'''
    return create_lambda_function_context(function_name)

# Data
@pytest.fixture()
def mock_data(data=DATA) -> ThingData:
    '''Return function event data'''
    with open(data) as f:
        return ThingData(**json.load(f))

@pytest.fixture()
def data_schema(data_schema=DATA_SCHEMA):
    '''Return a data schema'''
    with open(data_schema) as f:
        return json.load(f)
# Event
@pytest.fixture()
def mock_event(e=EVENT) -> APIGatewayProxyEvent:
    '''Return a function event'''
    with open(e) as f:
        return APIGatewayProxyEvent(json.load(f))

@pytest.fixture()
def event_schema(schema=EVENT_SCHEMA):
    '''Return an event schema'''
    with open(schema) as f:
        return json.load(f)

# Output
@pytest.fixture()
def mock_expected_output(output=OUTPUT) -> Output:
    '''Return a function output'''
    with open(output) as f:
        return Output(**json.load(f))

@pytest.fixture()
def expected_output_schema(output_schema=OUTPUT_SCHEMA):
    '''Return an output schema'''
    with open(output_schema) as f:
        return json.load(f)

# Response
@pytest.fixture()
def mock_expected_response(response=RESPONSE) -> ResponseBody:
    '''Return response'''
    with open(response) as f:
        return ResponseBody(**json.load(f))

@pytest.fixture()
def expected_response_schema(response_schema=RESPONSE_SCHEMA):
    '''Return an output schema'''
    with open(response_schema) as f:
        return json.load(f)


# AWS Clients
@pytest.fixture()
def aws_credentials() -> None:
    '''Mocked AWS Credentials for moto.'''
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture()
def mocked_aws(aws_credentials):
    '''Mock all AWS interactions'''
    with mock_aws():
        yield

@pytest.fixture()
def mock_ddb_table_client(mocked_aws) -> Generator[Table , None, None]:
    '''Return the DDB table client'''
    ddb_table_name = 'MockDdbTable'
    ddb_resource: DynamoDBServiceResource = boto3.resource('dynamodb', 'us-east-1')
    ddb_resource.create_table(
        TableName=ddb_table_name,
        KeySchema=[
            {
                'AttributeName': 'pk',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'sk',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'pk',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'sk',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    ddb_table = ddb_resource.Table(ddb_table_name)
    yield ddb_table

# Function
@pytest.fixture()
def mock_fn(
    mocked_aws,
    mock_ddb_table_client: Table,
    mocker: MockerFixture,
) -> Generator[ModuleType, None, None]:
    '''Patch the environment variables for the function'''
    import src.handlers.UpsertThingItem.function as fn

    mocker.patch(
        'src.handlers.UpsertThingItem.function.DDB_TABLE',
        mock_ddb_table_client
    )
    yield fn


### Data validation
def test_validate_data(mock_data, data_schema):
    '''Test data against schema'''
    jsonschema.Draft7Validator(asdict(mock_data), data_schema)

def test_validate_event(mock_event, event_schema):
    '''Test event against schema'''
    jsonschema.Draft7Validator(mock_event._data, event_schema)

def test_validate_expected_data(mock_expected_output, expected_output_schema):
    '''Test output against schema'''
    jsonschema.Draft7Validator(asdict(mock_expected_output), expected_output_schema)

def test_validate_expected_response(mock_expected_response, expected_response_schema):
    '''Test response against schema'''
    jsonschema.Draft7Validator(asdict(mock_expected_response), expected_response_schema)


### Tests
def test_handler(
    mock_fn: ModuleType,
    mock_event: APIGatewayProxyEvent,
    mock_context,
    mocked_aws,
    mock_data: ThingData,
    mock_expected_output: Output,
    mock_expected_response: ResponseBody,
    mock_ddb_table_client: Table,
):
    '''Test calling handler'''
    # Insert data into event
    mock_event._data['body'] = json.dumps(asdict(mock_data))
    mock_expected_response.request_id = mock_context.aws_request_id

    keys = get_keys_from_id(mock_event.path_parameters.get('id'))
    # Insert data into table
    mock_ddb_table_client.put_item(
        Item={
            'pk': keys.pk,
            'sk': keys.pk
        }
    )

    output = mock_fn.handler(mock_event, mock_context)

    output_obj = Output(**output)
    assert output_obj.statusCode == mock_expected_output.statusCode

    response_obj = ResponseBody(**json.loads(output_obj.body))
    assert response_obj == mock_expected_response


def test__upsert_item(
    mock_fn: ModuleType,
    mock_data: ThingData,
    mock_ddb_table_client: Table,
):
    '''Test upsert item'''
    # Insert data into table
    mock_ddb_table_client.put_item(
        Item={
            'pk': '1234',
            'sk': '1234',
        }
    )

    item_keys = ThingItemKeys(**{'pk': '1234', 'sk': '1234'})
    item_data = mock_data
    mock_fn._upsert_item(item_keys, item_data)


def test__upsert_item_fails_when_item_does_not_exist(
    mock_fn: ModuleType,
    mock_data: ThingData,
    mock_ddb_table_client: Table,
):
    '''Test upsert item'''
    item_keys = ThingItemKeys(**{'pk': '1234', 'sk': '1234'})
    item_data = mock_data
    with pytest.raises(
        mock_ddb_table_client.meta.client.exceptions.ConditionalCheckFailedException
    ):
        mock_fn._upsert_item(item_keys, item_data)