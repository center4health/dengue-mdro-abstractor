from data.utils import (
    concatenate_notes
)

class DengueForm:
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
        self.answers['birth_date'] = self.data['demographics'][0]['birth_date']
        dengue_results = [d for d in self.data['observations'] if 'Dengue' in d['feature']]
        dengue_str = ''
        for d in dengue_results:
            dengue_str += (
                "DENGUE FEVER VIRUS ANTIBODIES, IGG & IGM, BLOOD: "
                + str(d['value'])
                + ' '
                + d['unit'] 
                + " @ "
                + d['timestamp']
            )
            dengue_str += '\n'

        self.answers['dengue_results'] = dengue_str

        response = self.llm(
            notes
        )

        for k,v in response.items():
            self.answers[k] = v

        return self.answers
