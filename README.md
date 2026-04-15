# Public Health Chart Abstraction

An LLM-based pipeline that automates public health chart abstraction from FHIR-formatted patient medical records. Currently supports two workflows:

1. **Dengue Fever Case Reporting** — extracts clinical summary, travel history, and vaccination history for dengue surveillance
2. **MDRO Transfer Form Completion** — auto-fills infection control transfer forms for patients with multidrug-resistant organisms (MDROs)

Both pipelines use RAG (Retrieval-Augmented Generation) with a locally hosted LLaMA 3.1 model via vLLM to extract structured information from unstructured clinical notes.

---

## How It Works

```
FHIR Patient Data (JSON)
        │
        ▼
  RAG (ChromaDB + InstructorEmbeddings)
        │
        ▼
  LLM (LLaMA 3.1 via vLLM + Outlines)
        │
        ▼
  Structured Output (JSON / HTML form)
```

- Clinical notes are chunked and embedded into a vector store (ChromaDB)
- Relevant chunks are retrieved per question via semantic search
- LLaMA 3.1 generates structured JSON responses, constrained by schema using [Outlines](https://github.com/outlines-dev/outlines)

---

## Project Structure

```
.
├── main_dengue.py          # Entry point: dengue case report pipeline
├── main_mdro.py            # Entry point: MDRO transfer form pipeline
├── data/
│   ├── load_dengue.py      # Load dengue patient FHIR data
│   ├── load_mdro.py        # Load MDRO/transfer patient FHIR data
│   ├── events.py           # Medication order/MAR processing
│   ├── utils.py            # Shared utilities (note concatenation, datetime)
│   └── logger.py           # Logging setup
├── llm/
│   ├── llm_dengue.py       # LLM + RAG class for dengue pipeline
│   └── llm_mdro.py         # LLM + RAG class for MDRO pipeline
├── measures/
│   ├── dengue.py           # DengueForm: question logic for dengue abstraction
│   └── transfer.py         # TransferForm: question logic for MDRO transfer form
├── inputs/
│   └── medications.csv     # Reference list of antibiotics
└── outputs/                # Generated outputs (git-ignored)
    ├── dengue/             # dump.txt per run
    └── transfer/           # Per-patient JSON + HTML forms
```

---

## Requirements

- Python 3.10+
- GPU with sufficient VRAM (tested on A10G with LLaMA 3.1 8B)
- LLaMA 3.1 model weights (locally downloaded)

Install dependencies:

```bash
pip install vllm outlines langchain langchain-experimental chromadb \
            InstructorEmbedding jinja2 pandas python-dotenv
```

---

## Setup

1. Copy `.env.example` to `.env` and set your model path:

```bash
cp .env.example .env
```

```
LLM_MODEL_PATH=/path/to/your/llama3.1/model/
```

2. Place your FHIR-formatted patient data in `inputs/`:
   - `inputs/dengue_patient_features.json` — for dengue pipeline
   - `inputs/transfer_patient_features.json` — for MDRO pipeline

---

## Usage

**Dengue case report:**
```bash
python main_dengue.py
```
Output: `outputs/dengue/dump.txt`

**MDRO transfer form:**
```bash
python main_mdro.py
```
Output: `outputs/transfer/<csn>.json` and `outputs/transfer/<csn>.html`

---

## Input Data Format

Expected FHIR-based JSON structure per patient:

```json
{
  "demographics": [{"mrn": "...", "csn": "...", "first_name": "...", "last_name": "...", "birth_date": "..."}],
  "binary": [{"note": "...", "note_type": "...", "created_time": "..."}],
  "observations": [{"feature": "...", "value": "...", "unit": "...", "timestamp": "..."}],
  "medication_orders": [...],
  "immunizations": [...],
  "lda": [...],
  "flag": [...]
}
```

---

## Notes
- Designed to run on AWS EC2 with GPU instances, but portable to any environment with a compatible GPU
