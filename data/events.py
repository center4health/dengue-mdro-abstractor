import pandas as pd
import re
from data.utils import to_datetime

def get_med_times(
    data: dict, 
    medfile: str,  
    medclass='antibiotic',
    route_of_administration=(
        "intravenous", 
        "intramuscular", 
        "intraosseous"
    )
) -> dict:
    '''
    Returns order and administration information for a 
    specified class of medications. 
    '''

    if 'medication_orders' not in data.keys():
        return {
            'names': [], 
            'order_times': [], 
            'admin_start_times': [], 
            'admin_end_times': [],
            'admin_times': [],
            'routes': [],
            'dosage_text': [],
            'doses': []
        } 

    med_info = pd.read_csv(medfile)
    med_list = (
        med_info
        .loc[med_info['class'] == medclass]
        .name
        .str
        .lower()
        .values
    )
    med_str = '|'.join(med_list)
    
    order_times = []
    order_start_times = []
    order_end_times = []
    admin_start_times = []
    admin_end_times = []
    routes = []
    names = []
    dosage_text = []
    doses = []
    all_admin_times = []

    for d in data['medication_orders']:
        if "route" in d.keys():
            route = d['route'].lower()
            if route in route_of_administration:
                med = re.search(med_str, d['medication'].lower())
                if med is not None:
                    routes.append(route)
                    order_times.append(d['timestamp'])
                    order_start_times.append(d.get('start_date'))
                    order_end_times.append(d.get('end_date'))
                    
                    names.append(med.group(0).title())
                    dosage_text.append(d.get('dosage_text'))

                    # Determine dosage and administration information 
                    # from the MAR.  This is involved since dosages
                    # can be adjusted, etc.
                    # TODO: Make this more generalizable for all 
                    # units of measurement.
                    dose = None
                    max_admin_time = None
                    min_admin_time = None
                    admin_times = []
                    if "mar" in d.keys():
                        admin_times = [
                            d['AdministrationInstant'] 
                            for d in d['mar'] 
                            if d['Action'] in ('New Bag', 'Given')
                        ]
                        min_admin_time = min(admin_times, default=None)
                        
                        completion_times = [
                            d['AdministrationInstant'] 
                            for d in d['mar'] 
                            if d['Action'] in ('Completed', 'Stopped')
                        ]

                        if completion_times:
                            max_admin_time = max(completion_times)
                        else:
                            max_admin_time = None
                    
                        dose = 0
                        start_time = None
                        end_time = None
                        rate = None
                        admins = sorted(
                            d['mar'], 
                            key=lambda x: x['AdministrationInstant']
                        )
                        for a in admins:
                            if a['Dose'] is not None:
                                dose += float(a['Dose']['Value'])
                            elif a['Action'] == 'New Bag':
                                if a['Rate'] and a['Rate']['Unit'] == 'mL/hr':
                                    start_time = to_datetime(
                                        a['AdministrationInstant']
                                    )
                                    rate = float(a['Rate']['Value'])
                            elif a['Action'] in ('Completed', 'Stopped'):
                                end_time = to_datetime(
                                    a['AdministrationInstant']
                                )
                                if start_time and end_time and rate:
                                    dose += (
                                        rate
                                        *(end_time - start_time)
                                        .total_seconds()
                                        /3600
                                    )

                        # If no end is documented, use the planned end time
                        if rate and not dose and d.get('end_date'):
                            dose = (
                                rate
                                *(to_datetime(d['end_date']) - start_time)
                                .total_seconds()
                                /3600
                            )


                    doses.append(dose)
                    admin_start_times.append(min_admin_time)
                    admin_end_times.append(max_admin_time)
                    all_admin_times.append(admin_times)

    return {
        'names': names, 
        'order_times': order_times, 
        'admin_start_times': admin_start_times, 
        'admin_end_times': admin_end_times,
        'admin_times': all_admin_times,
        'routes': routes,
        'dosage_text': dosage_text,
        'doses': doses,
        'order_start_times': order_start_times,
        'order_end_times': order_end_times,
    }