#!/usr/bin/env python3

import lightmeter
import pandas as pd
import json

_tableTypes = {
    'integer': 'int64',
    'number': 'float64',
    'boolean': 'bool',
    'datetime': 'datetime64[ns]',
    'duration': 'timedelta64[ns]',
    'any': 'categorical',
    'str': 'object'
}

def from_json(file):
    try:
        with open(file, 'r') as f:
            jsd = json.load(f)
    except TypeError:
        jsd = json.load(file)
    indexName = jsd['schema']['primaryKey']
    dtype = {f['name']: _tableTypes[f['type']] for f in jsd['schema']['fields']}
    cols = [f['name'] for f in jsd['schema']['fields']]
    df = pd.DataFrame(jsd['data'], columns=cols)
    df = df.astype(dtype=dtype).set_index(indexName)
    return df
