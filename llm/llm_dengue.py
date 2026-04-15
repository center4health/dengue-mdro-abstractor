from langchain.vectorstores import Chroma
from collections import defaultdict, Counter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceInstructEmbeddings
import vllm
import re
from langchain_experimental.pydantic_v1 import BaseModel
from outlines import models, generate
import gc
import os
from typing import List
from dotenv import load_dotenv

from data.logger import logger

load_dotenv()

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

LLM_MODEL_PATH = os.environ.get("LLM_MODEL_PATH")
if not LLM_MODEL_PATH:
    raise EnvironmentError("LLM_MODEL_PATH is not set. Check your .env file.")

class DENGUE_JSON(BaseModel):
    clinical_summary: str
    travel_history: str
    vaccination_history: str

class LLM:
    def __init__(self, prompt_template) -> None:
        
        logger.info("Initializing Embedding model")

        self.embedding = HuggingFaceInstructEmbeddings(
            model_name='hkunlp/instructor-large'
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, chunk_overlap=100, separators=["."]
        )
        
        self.context_length = 8192
        self.llm = vllm.LLM(
            LLM_MODEL_PATH,
            trust_remote_code=True,
            gpu_memory_utilization=0.85,
            max_model_len=self.context_length,
        )
        self.llm = models.VLLM(self.llm)
        self.llm_engine = generate.json(self.llm, DENGUE_JSON)
        self.sampling_params = vllm.SamplingParams(
                                      temperature=0.1,
                                      max_tokens=6000
                                      )

        self.prompt_template = prompt_template

        logger.info("LLM and Embedding model loaded onto memory")

    def __call__(
        self, 
        data, 
        rag=True, 
        filters=None,
        n_runs=1
    ) -> dict:
        llm_response = None
        context = None
        if rag:
            all_splits = self.text_splitter.split_text(data)
            if filters:
                all_splits_filtered = []
                for chunk in all_splits:
                    matches = []
                    for fil in filters:
                        match = re.search(
                            fil, 
                            chunk, 
                            flags=re.IGNORECASE
                        )
                        if match:
                            matches.append(fil)
                    
                    if matches:
                        all_splits_filtered.append(chunk)
                
                all_splits = all_splits_filtered

            vectorstore = Chroma.from_texts(
                texts=all_splits, embedding=self.embedding
            )
            retriever=vectorstore.as_retriever(k=12)
            embedding_prompt = self.prompt_template.format(
                context="Determined per instructions below."
            )
            context = retriever.invoke(embedding_prompt)
            vectorstore.delete_collection()
            gc.collect()
        else:
            context = data

        prompt = self.prompt_template.format(
                context=context
                )
        prompts = [prompt for _ in range(n_runs)] 
                
        
        while True:
            try:
                llm_response = self.llm_engine(prompts, sampling_params=self.sampling_params)
                break
            except:
                print('failing!')
                continue
        print(llm_response)
        
        gc.collect()

        return llm_response
