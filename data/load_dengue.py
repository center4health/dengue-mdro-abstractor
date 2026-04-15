import pandas as pd
import json
from collections import defaultdict
import datetime
import json

from data.logger import logger

def get_data():
    '''Pull from external sources.'''
    # TODO: Make this DB queries.

    fhir_data = pd.read_json("./inputs/dengue_patient_features.json")
    fhir_data = [json.loads(d) for d in fhir_data['features']]

    data = defaultdict(dict)
    i = 0
    for d in fhir_data:
        mrn = d['demographics'][0]['mrn']
        csn = d['demographics'][0]['csn']

        data[csn] = d
        i += 1

    print(i)
    return data
