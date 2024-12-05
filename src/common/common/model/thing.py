from dataclasses import dataclass
from typing import Optional
from uuid import uuid4 as uuid

COLLECTION_NAME = 'thing'

@dataclass
class BaseThingData:
    '''Base attributes of Thing type'''
    pass


@dataclass
class ThingData(BaseThingData):
    '''Thing data'''
    id: Optional[str] = None

@dataclass
class ThingItemKeys:
    '''Thing DDB item keys'''
    pk: str
    sk: str

    def get_data(self):
        return { k:v for (k, v) in self.__dict__.items() if k not in ThingItemKeys.__dict__.keys() }

@dataclass
class ThingItem(ThingData, ThingItemKeys):
    '''Thing DDB item'''
    id: str

    def get_data(self):
        return { k:v for (k, v) in self.__dict__.items() if k not in ['sk', 'pk'] }

def create_keys() -> ThingItemKeys:
    '''Create keys for DDB'''
    key = '{}#{}'.format(COLLECTION_NAME, str(uuid()))
    return ThingItemKeys(**{'pk': key, 'sk': key})

def get_keys_from_id_from_id(_id: str) -> ThingItemKeys:
    '''Get keys for DDB'''
    key = '{}#{}'.format(COLLECTION_NAME, _id)
    return ThingItemKeys(**{'pk': key, 'sk': key})

def get_id_from_keys(keys: ThingItemKeys) -> str:
    '''Get id from keys'''
    return keys.pk.split('#')[1]