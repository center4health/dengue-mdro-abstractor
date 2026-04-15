from datetime import datetime
import re
from collections import defaultdict

def concatenate_notes(notes) -> str:
    '''
    Concatenates a list of JSON binary records, their creation time,
    and their category, to return a long single string.
    '''
    all_notes = ''
    for note in notes:
        time = note['created_time']
        date = time.split('T')[0].replace('-', '/')
        
        if "T" in time:
            time = time.split('T')[1][:-1]
        else:
            time = 'N/A'
            
        if 'note_type' not in note.keys():
            note_type = ''
        else:
            note_type = note['note_type']
        
        txt = 'Note Type: ' + note_type + '\n'
        txt += 'Note Created Date: '+ date + '\n'
        txt += 'Note Created Time: ' + time + '\n'
        txt += note['note'] + '\n'

        all_notes += '\n' + txt
    
    return all_notes  


def return_tuples_in_range(
    data: list, 
    lower, 
    upper,
    i=0
) -> list:
    '''
    Simple helper function that filters a list of tuples based on
    the lower and upper thresholds and the value in the ith position
    of the tuple.
    '''
    data = [
        v for v 
        in data 
        if v[i] >= lower and v[i] <= upper
    ]
    return data
 

def to_datetime(date: str) -> datetime:
    return datetime.fromisoformat(date.replace('Z', ''))

