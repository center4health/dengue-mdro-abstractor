from measures.dengue import dengue
from llm.llm_dengue import LLM
from collections import defaultdict
import json
import glob
import os

from data.load_dengue import get_data
from data.logger import logger

from langchain.prompts import PromptTemplate


def main():
    data = get_data()
    PROMPT_TEMPLATE = PromptTemplate(template =
    """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are a dengue fever public health investigator. Your task is to review a patient's medical
    chart and complete the specified fields in the investigator checklist. Do not infer or take a likely guess. Only answer based on objective evidence in the medical chart.
    <|start_header_id|>user<|end_header_id|>
    RELEVANT SECTIONS FROM THE MEDICAL CHART: {context}

    INVESTIGATOR INSTRUCTIONS:
    1. clinical_summary: Please provide a concise and relevant clinical summary of the patient with enough information for an MD to make an informed decision.
    2. travel_history: Please describe the patient's travel history and explicitly documented mosquito exposure information.
    3. vaccination_history: Please describe the patient's vaccination history.

    BAD EXAMPLE:
    "He reports that he had no mosquito exposure information explicitly documented in the medical chart." This is bad because it is not possible for a patient to report on the lack of documentation in their chart.

    GOOD EXAMPLE:
    "There is no explicit documentation of mosquito exposure."

    OUTPUT FORMAT: Return the answer as a JSON object following the format,
    {{"clinical_summary": str, "travel_history": str, "vaccination_history": str}}.<|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    ANSWER:
    """,
    input_variables = ["context"]
    )

    llm = LLM(PROMPT_TEMPLATE)
    previous_outputs = glob.glob('./outputs/dengue/*')
    previous_outputs = [
        os.path.splitext(os.path.basename(p))[0]
        for p in previous_outputs
    ]

    all_answers = defaultdict(dict)
    llm_io = defaultdict(dict)
    os.makedirs('./outputs/dengue', exist_ok=True)
    f = open('./outputs/dengue/dump.txt', 'a')
    for csn, csn_data in data.items():
        questionnaire = dengue.DengueForm(csn_data, llm)
        answers = questionnaire.start()

        txt = f'''MRN:  {answers['mrn']}
        Name:  {answers['name']}
        Date of Birth" {answers['birth_date']}

        Dengue PCR, IgG, and/or IgM result(s):
        {answers['dengue_results']}

        Clinical Summary:
        {answers['clinical_summary']}

        Travel History:
        {answers['travel_history']}

        Vaccination History:
        {answers['vaccination_history']}
        _________________________________________

        '''
        f.write(txt.replace('   ', ''))

    f.close()


if __name__ == '__main__':
    flag = False
    logger.info("Starting Dengue Case Report Validation Run")
    main()
    logger.info("Ending Dengue Case Report Validation Run")
