from llm.llm_mdro import LLM
from collections import defaultdict
import json
import glob
import os
from measures.transfer import transfer

from data.load_mdro import get_data
from data.logger import logger

from langchain.prompts import PromptTemplate
from jinja2 import Template

def main():
    patient_data = get_data()

    PROMPT_TEMPLATE = PromptTemplate(template =
        """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

        You are a public health chart abstractor. Your task is to review patient's medical
        notes and answer the given clinical question following the
        abstraction instructions.
        Generate clear rationale to your answer by thinking step-by-step.<|eot_id|>

        <|start_header_id|>user<|end_header_id|>
        MEDICAL NOTES: {context}.
        QUESTION: {question}
        OUTPUT FORMAT: Return the answer as a JSON object following the format,
        {{"rationale": str, "option": str}}.<|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>
        """,
        input_variables = ["context", "question"]
    )

    llm = LLM(PROMPT_TEMPLATE)
    previous_outputs = glob.glob('./outputs/transfer/*')
    previous_outputs = [
        os.path.splitext(os.path.basename(p))[0]
        for p in previous_outputs
    ]

    all_answers = defaultdict(dict)
    llm_io = defaultdict(dict)

    os.makedirs('./outputs/transfer', exist_ok=True)

    for csn, csn_data in patient_data.items():
        questionnaire = transfer.TransferForm(csn_data, llm)
        answers = questionnaire.start()

        with open('./measures/transfer/form.html', 'r', encoding='utf-8') as f:
            template_str = f.read()

        template = Template(template_str)

        form_data = {
            'patient_name': answers['name'],
            'dob': answers['date of birth'],
            'mrn': answers['mrn'],
            'transfer_date': answers['transfer_date'],
            'receiving_facility': "UCSD HEALTH SYSTEM SERVICE AREA",
            'sending_facility': answers['sending_facility']['option'],

            'on_precautions': True if answers['precautions'] else False,
            'not_on_precautions': False if answers['precautions'] else True,
            'precautions_airborne': answers['precautions_airborne'],
            'precautions_contact': answers['precautions_contact'],
            'precautions_droplet': answers['precautions_droplet'],
            'precautions_enhanced': answers.get('precautions_enhanced', False),

            'transfer_reason_na': False,
            'transfer_reason': answers['reason_for_transfer']['option'],
            'symptoms_na': False,
            'symptom_diarrhea': True if answers['diarrhea']['option'] == 'Y' else False,
            'symptom_respiratory': True if answers['resp_secretions']['option'] == 'Y' else False,
            'change_in_mental_status': True if answers['change_in_mental_status']['option'] == 'Y' else False,
            'change_in_wound_drainage': True if answers['change_in_wound_drainage']['option'] == 'Y' else False,
            'incontinent_urine': True if answers['incontinent_urine']['option'] == 'Y' else False,
            'vomiting': True if answers['vomiting']['option'] == 'Y' else False,
            'infectious_rash': True if answers['infectious_rash']['option'] == 'Y' else False,

            'mental_status_at_transfer_alert': True if answers['mental_status_at_transfer']['option'] == 'Alert' else False,
            'mental_status_at_transfer_not_alert': True if answers['mental_status_at_transfer']['option'] == 'Not Alert' else False,
            'mental_status_at_transfer_oriented': True if answers['mental_status_at_transfer']['option'] == 'Oriented' else False,
            'mental_status_at_transfer_disoriented': True if answers['mental_status_at_transfer']['option'] == 'Disoriented' else False,

            'baseline_mental_status_alert': True if answers['baseline_mental_status']['option'] == 'Alert' else False,
            'baseline_mental_status_not_alert': True if answers['baseline_mental_status']['option'] == 'Not Alert' else False,
            'baseline_mental_status_oriented': True if answers['baseline_mental_status']['option'] == 'Oriented' else False,
            'baseline_mental_status_disoriented': True if answers['baseline_mental_status']['option'] == 'Disoriented' else False,

            'pre_resp_secretion': True if answers['pre_resp_secretion']['option'] == 'Y' else False,
            'pre_cloudy_urine': True if answers['pre_cloudy_urine']['option'] == 'Y' else False,

            'speech_verbal': True if answers['non_verbal']['option'] == 'N' else False,
            'speech_non_verbal': True if answers['non_verbal']['option'] == 'Y' else False,

            'has_mdros': True if any([v for v in answers['organisms'].values()]) else False,
            'exposed_mdros': False,

            'org_cauris': answers['org_cauris'],
            'org_cauris_carbapenemase': answers['org_cauris_carbapenemase'],
            'org_cauris_source': answers['org_cauris_source'],
            'org_cauris_date': answers['org_cauris_date'],

            'org_cdiff': answers['org_cdiff'],
            'org_cdiff_carbapenemase': answers['org_cdiff_carbapenemase'],
            'org_cdiff_source': answers['org_cdiff_source'],
            'org_cdiff_date': answers['org_cdiff_date'],

            'org_crab': answers['org_crab'],
            'org_crab_carbapenemase': answers['org_crab_carbapenemase'],
            'org_crab_source': answers['org_crab_source'],
            'org_crab_date': answers['org_crab_date'],

            'org_cre': answers['org_cre'],
            'org_cre_carbapenemase': answers['org_cre_carbapenemase'],
            'org_cre_source': answers['org_cre_source'],
            'org_cre_date': answers['org_cre_date'],

            'org_crpa': answers['org_crpa'],
            'org_crpa_carbapenemase': answers['org_crpa_carbapenemase'],
            'org_crpa_source': answers['org_crpa_source'],
            'org_crpa_date': answers['org_crpa_date'],

            'org_esbl': answers['org_esbl'],
            'org_esbl_carbapenemase': answers['org_esbl_carbapenemase'],
            'org_esbl_source': answers['org_esbl_source'],
            'org_esbl_date': answers['org_esbl_date'],

            'org_mrsa': answers['org_mrsa'],
            'org_mrsa_carbapenemase': answers['org_mrsa_carbapenemase'],
            'org_mrsa_source': answers['org_mrsa_source'],
            'org_mrsa_date': answers['org_mrsa_date'],

            'org_vre': answers['org_vre'],
            'org_vre_carbapenemase': answers['org_vre_carbapenemase'],
            'org_vre_source': answers['org_vre_source'],
            'org_vre_date': answers['org_vre_date'],

            'on_antibiotics': True if answers['abx']['names'] else False,
            'not_on_antibiotics': False if answers['abx']['names'] else True,

            "abx_1_name": answers['abx_1_name'],
            "abx_1_dose_text": answers['abx_1_dose_text'],
            "abx_1_start": answers['abx_1_start'],
            "abx_1_stop": answers['abx_1_stop'],

            "abx_2_name": answers['abx_2_name'],
            "abx_2_dose_text": answers['abx_2_dose_text'],
            "abx_2_start": answers['abx_2_start'],
            "abx_2_stop": answers['abx_2_stop'],

            "abx_3_name": answers['abx_3_name'],
            "abx_3_dose_text": answers['abx_3_dose_text'],
            "abx_3_start": answers['abx_3_start'],
            "abx_3_stop": answers['abx_3_stop'],

            'device_central_line': True if answers['central_line']['option'] == 'Y' else False,
            'device_central_line_date': '',
            'hemodialysis_catheter': True if answers['hemodialysis_catheter']['option'] == 'Y' else False,
            'mechanical_ventilation': True if answers['mechanical_ventilation']['option'] == 'Y' else False,
            'feeding_tube': True if answers['feeding_tube']['option'] == 'Y' else False,
            'suprapubic_catheter': True if answers['suprapubic_catheter']['option'] == 'Y' else False,
            'tracheostomy_tube': True if answers['tracheostomy_tube']['option'] == 'Y' else False,
            'urinary_catheter': True if answers['urinary_catheter']['option'] == 'Y' else False,
            'urostomy_tube': True if answers['urostomy_tube']['option'] == 'Y' else False,
            'wound_vac': True if answers['wound_vac']['option'] == 'Y' else False,

            'immu_y': True if answers['has_immunization'] else False,
            'immu_n': False if answers['has_immunization'] else True,

            'immu_pneumo_yn': answers['immu_pneumo_yn'],
            'immu_pneumo_date': answers['immu_pneumo_date'],

            'immu_covid_yn': answers['immu_covid_yn'],
            'immu_covid_date': answers['immu_covid_date'],

            'immu_flu_yn': answers['immu_flu_yn'],
            'immu_flu_date': answers['immu_flu_date'],
        }

        output = template.render(data=form_data)

        output_file = './outputs/transfer/' + str(csn) + '.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)

        print(f"Filled form written to {output_file}")

        with open('./outputs/transfer/' + str(csn) + '.json', 'w') as f:
            json.dump(answers, f, indent=4)

if __name__ == '__main__':
    flag = False
    logger.info("Starting MDRO Validation Run")
    main()
    logger.info("Ending MDRO Validation Run")
