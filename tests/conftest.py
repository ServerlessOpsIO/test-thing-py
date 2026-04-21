import os
import sys

from collections import namedtuple

import pytest


# NOTE: Hack so we can test against local functions without installing them
# into the venv as pytest expects
#
# ref: https://github.com/pytest-dev/pytest/issues/2421#issuecomment-403724503
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture()
def lambda_function_context():
    def _factory(function_name: str, object_name: str = 'LambdaContext'):
        context_info = {
            'aws_request_id': '00000000-0000-0000-0000-000000000000',
            'function_name': function_name,
            'invoked_function_arn': f'arn:aws:lambda:us-east-1:012345678910:function:{function_name}',
            'memory_limit_in_mb': 128,
        }
        Context = namedtuple(object_name, context_info.keys())
        return Context(*context_info.values())
    return _factory