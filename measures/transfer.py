from data.utils import (
    concatenate_notes,
    to_datetime
)
from data.events import get_med_times
from zoneinfo import ZoneInfo
import datetime
from difflib import SequenceMatcher

class TransferForm:
    def __init__(self, data, llm):
        self.data = data
        self.llm = llm
        self.answers = {}
        self.log = {}

    def start(self):
        notes = concatenate_notes(self.data['binary'])

        self.answers['mrn'] = self.data['demographics'][0]['mrn']
        self.answers['name'] = (
            self.data['demographics'][0]['first_name']
            + ' '
            + self.data['demographics'][0]['last_name']
        )
        self.answers['date of birth'] = self.data['demographics'][0]['birth_date']

        self.answers['precautions'] = False
        self.answers['precautions_contact'] = False
        self.answers['precautions_droplet'] = False
        self.answers['precautions_airborne'] = False

        if "flag" in self.data.keys():
            flags = [v['name'].lower() for v in self.data['flag'] if v['status'] == 'active']
            if flags:
                self.answers['precautions'] = True
            
            for f in flags:
                if "contact" in f:
                    self.answers['precautions_contact'] = True
                elif "airborne" in f:
                    self.answers['precautions_airborne'] = True
                elif "droplet" in f:
                    self.answers['precautions_droplet'] = True
            

        self.answers['transfer_date'] = (
            to_datetime(self.data['demographics'][0]['hosp_admission_date'])
            .replace(tzinfo=ZoneInfo('UTC'))
            .astimezone(ZoneInfo('America/Los_Angeles'))
            .date()
            .isoformat()
        )

        prompt = "What is the name of the specific facility that the patient was transferred from?"
        self.answers['sending_facility'] = self.llm(
            notes,
            prompt,
            filters=['transferred from']
        )

        prompt = "What is the reason for transfer documented in the notes?"
        self.answers['reason_for_transfer'] = self.llm(
            notes,
            prompt,
        )

        YN_suffix = '''
        ANSWER OPTIONS:
        Y - Yes
        N - No

        '''
        prefix = "Is there explicit documentation that the patient has symptoms or clinical status of "
        diarrhea = prefix + "Acute diarrhea or incontinent stool?" + YN_suffix
        resp_secretions = prefix + "change in respiratory secretions?" + YN_suffix
        change_in_mental_status = prefix + "change in mental status?" + YN_suffix
        change_in_wound_drainage = prefix + "change in wound drainage (e.g. purulence)?" + YN_suffix
        incontinent_urine = prefix + "incontinent of urine?" + YN_suffix
        vomiting = prefix + "vomiting?" + YN_suffix
        infectious_rash = prefix + "rash consistent with an infectious process (e.g. vascular)?" + YN_suffix


        self.answers['diarrhea'] = self.llm(
            notes,
            diarrhea,
        )
        self.answers['resp_secretions'] = self.llm(
            notes,
            resp_secretions,
        )
        self.answers['change_in_mental_status'] = self.llm(
            notes,
            change_in_mental_status,
        )
        self.answers['change_in_wound_drainage'] = self.llm(
            notes,
            change_in_wound_drainage,
        )
        self.answers['incontinent_urine'] = self.llm(
            notes,
            incontinent_urine,
        )
        self.answers['vomiting'] = self.llm(
            notes,
            vomiting,
        )
        self.answers['infectious_rash'] = self.llm(
            notes,
            infectious_rash,
        )


        prefix = "Does the patient currently have this device: "
        central_line = prefix + "Central line/PICC" + YN_suffix + "EXAMPLES: \n CVC Triple Lumen = Y \n"
        hemodialysis_catheter = prefix + "Hemodialysis catheter" + YN_suffix  + "EXAMPLES: \n CVC Triple Lumen = N \n"
        mechanical_ventilation = prefix + "Mechanical ventilation" + YN_suffix
        feeding_tube = prefix + "Percutaneous gastrostomy feeding tube" + YN_suffix
        suprapubic_catheter = prefix + "Suprapubic catheter" + YN_suffix
        tracheostomy_tube = prefix + "Tracheostomy tube" + YN_suffix
        urinary_catheter = prefix + "Urinary catheter" + YN_suffix
        urostomy_tube = prefix + "Urostomy tube" + YN_suffix
        wound_vac = prefix + "Wound vac" + YN_suffix + "EXAMPLES: \n Dressing Type = N \n"

        lda_text = 'ALL DEVICES:\n'
        ldas = set([v['code']['text'] for v in self.data['lda']])
        for v in ldas:
            lda_text += v + '\n'

        self.answers['central_line'] = self.llm(
            lda_text,
            central_line,
        )
        self.answers['hemodialysis_catheter'] = self.llm(
            lda_text,
            hemodialysis_catheter,
        )
        self.answers['mechanical_ventilation'] = self.llm(
            lda_text,
            mechanical_ventilation,
        )
        self.answers['feeding_tube'] = self.llm(
            lda_text,
            feeding_tube,
        )
        self.answers['suprapubic_catheter'] = self.llm(
            lda_text,
            suprapubic_catheter,
        )
        self.answers['tracheostomy_tube'] = self.llm(
            lda_text,
            tracheostomy_tube,
        )
        self.answers['urinary_catheter'] = self.llm(
            lda_text,
            urinary_catheter,
        )

        self.answers['urostomy_tube'] = self.llm(
            lda_text,
            urostomy_tube,
        )
        self.answers['wound_vac'] = self.llm(
            lda_text,
            wound_vac,
        )

        last_year = datetime.datetime.now() - datetime.timedelta(days=365)
        last_year = last_year.date().isoformat()
        immunizations = [
            i['resource'] 
            for i in self.data['immunizations'] 
            if i['resource']['resourceType'] == 'Immunization'
            and i['resource']['status'] == 'completed'
        ]

        self.answers['has_immunization'] = False
        self.answers['immu_pneumo_yn'] = False
        self.answers['immu_pneumo_date'] = ''
        self.answers['immu_covid_yn'] = False
        self.answers['immu_covid_date'] = ''
        self.answers['immu_flu_yn'] = False
        self.answers['immu_flu_date'] = ''

        for v in immunizations:
            vaccine_date = v['occurrenceDateTime'].split('T')[0]
            if vaccine_date >= last_year:
                vaccine =  v['vaccineCode']['text'].lower()
                if "influen" in vaccine:
                    self.answers['immu_flu_yn'] = True
                    self.answers['immu_flu_date'] = vaccine_date
                    self.answers['has_immunization'] = True
                elif "covid" in vaccine:
                    self.answers['immu_covid_yn'] = True
                    self.answers['immu_covid_date'] = vaccine_date
                    self.answers['has_immunization'] = True
                elif "pneumo" in vaccine:
                    self.answers['immu_pneumo_yn'] = True
                    self.answers['immu_pneumo_date'] = vaccine_date
                    self.answers['has_immunization'] = True

            

        baseline_mental_status_prompt = '''
        What was the baseline mental status of the patient? Pick the best option between 'Alert', 'Not Alert', 'Oriented', 'Disoriented'
        '''
        self.answers['baseline_mental_status'] = self.llm(
            notes,
            baseline_mental_status_prompt,
        )

        mental_status_at_transfer_prompt = '''
        What was the mental status of the patient at transfer? Pick the best option between 'Alert', 'Not Alert', 'Oriented', 'Disoriented'
        '''
        self.answers['mental_status_at_transfer'] = self.llm(
            notes,
            mental_status_at_transfer_prompt,
        )

        self.answers['pre_cloudy_urine'] = self.llm(
            notes,
            "Is there explicit documentation of a pre-existing condition of cloudy urine?" +YN_suffix,
        )       

        self.answers['pre_resp_secretion'] = self.llm(
            notes,
            "Is there explicit documentation of a pre-existing condition of respiratory secretions?" +YN_suffix,
        ) 

        self.answers['non_verbal'] = self.llm(
            notes,
            "Is there explicit documentation that the patient was non-verbal on transfer?" +YN_suffix,
        )    
        self.answers['organisms'] = {
            'Candida auris': None,
            "Clostridiodes difficile": None,
            "Acinetobacter, multidrug-resistant": None,
            "Carbapenem-resistant enterobacterales": None,
            "Pseudomonas aeruginosa, multidrug-resistant": None,
            "Extended-spectrum beta-lactamase": None,
            "Methicillin resistant staphylococcus aureus": None,
            "Vancomycin resistant enterococcus": None
        }
        for d in self.data['observations']:
            if "value_code" in d.keys():
                for k in self.answers['organisms'].keys():
                    for v in d['value_code'].split('\r\n'):
                        if SequenceMatcher(None, k.lower(), v.lower()).ratio() > 0.8:
                            self.answers['organisms'][k] = {
                                "source": d['name'],
                                "date": d['timestamp']
                            }


        mapping = {
            'Candida auris': 'org_cauris',
            "Clostridiodes difficile": 'org_cdiff',
            "Acinetobacter, multidrug-resistant": 'org_crab',
            "Carbapenem-resistant enterobacterales": 'org_cre',
            "Pseudomonas aeruginosa, multidrug-resistant": 'org_crpa',
            "Extended-spectrum beta-lactamase": 'org_esbl',
            "Methicillin resistant staphylococcus aureus": 'org_mrsa',
            "Vancomycin resistant enterococcus": 'org_vre'
        }

        for k,v in mapping.items():
            self.answers[v] = True if self.answers['organisms'][k] else False
            self.answers[v + '_carbapenemase'] = ''
            if self.answers[v]:
                self.answers[v + '_source'] = self.answers['organisms'][k]['source']
                self.answers[v + '_date'] = (
                    to_datetime(self.answers['organisms'][k]['date'])
                    .replace(tzinfo=ZoneInfo('UTC'))
                    .astimezone(ZoneInfo('America/Los_Angeles'))
                    .replace(tzinfo=None)
                    .isoformat()
                )
            else:
                self.answers[v + '_source'] = ''
                self.answers[v + '_date'] = ''

        self.answers['abx'] = get_med_times(
            self.data, 
            './inputs/medications.csv', 
            medclass='antibiotic'
        )

        for i in range(3):
            label = "abx_" + str(i+1)
            if i < len(self.answers['abx']['names']):
                self.answers[label + "_name"] = self.answers['abx']['names'][i]
                self.answers[label + "_dose_text"] = self.answers['abx']['dosage_text'][i]
                self.answers[label + "_start"] = (
                    to_datetime(self.answers['abx']['order_start_times'][i])
                    .replace(tzinfo=ZoneInfo('UTC'))
                    .astimezone(ZoneInfo('America/Los_Angeles'))
                    .replace(tzinfo=None)
                    .isoformat()
                )

                self.answers[label + "_stop"] = (
                    to_datetime(self.answers['abx']['order_end_times'][i])
                    .replace(tzinfo=ZoneInfo('UTC'))
                    .astimezone(ZoneInfo('America/Los_Angeles'))
                    .replace(tzinfo=None)
                    .isoformat()
                )
            else:
                self.answers[label + "_name"] = ''
                self.answers[label + "_dose_text"] = ''
                self.answers[label + "_start"] = ''
                self.answers[label + "_stop"] = ''




        return self.answers
