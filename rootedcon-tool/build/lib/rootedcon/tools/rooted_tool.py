from promptflow import tool
from promptflow.connections import CustomConnection
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from peft import PeftModel, PeftConfig
import torch
import uuid
import requests
import re
import json

tokenizer = AutoTokenizer.from_pretrained("deepset/deberta-v3-base-injection")
lora_model = AutoModelForSequenceClassification.from_pretrained("deepset/deberta-v3-base-injection")

#config = PeftConfig.from_pretrained("rafalvar/mistral-lora-token-classification")
#model = AutoModelForSequenceClassification.from_pretrained(config.base_model_name_or_path)
#lora_model = PeftModel.from_pretrained(model, "rafalvar/mistral-lora-token-classification")

#tokenizer_id = "rafalvar/mistral-7b-ft-tc"
#tokenizer = AutoTokenizer.from_pretrained(tokenizer_id)

@tool
def check_prompt(ats: CustomConnection, input_text: str) -> str:
    
    # Classify prompts with a LLM model
    prompt = tokenizer(input_text, return_tensors="pt")
    with torch.no_grad():
        logits = lora_model(**prompt).logits
    predicted_class = logits.argmax().item()

    #Check language with Azure Translator 
    path = '/detect'
    constructed_url = ats.endpoint + path
    params = {
       'api-version': '3.0'
    }
    
    headers = {
        'Ocp-Apim-Subscription-Key': ats.key,
        'Ocp-Apim-Subscription-Region': ats.location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    body = [{
        'text': input_text
    }]
    
    request = requests.post(constructed_url, params=params, headers=headers, json=body)
    response = request.json()
    language = response[0]['language']

    #Detect regex
    regex=re.findall(r'\b([a-z]*(ignor|olvid|forg|stop|act)[a-z]*)\b', input_text, re.I)
    regex_check = ""
    if len(regex) == 0:
        regex_check = 0
    else:
        regex_check = 1

    #Check fields
    json_response = {}
    if predicted_class == 0 and language == "es" and regex_check == 0:
        json_response = {"check":"LEGIT", "class": predicted_class, "lang": language, "blocklist": regex_check}
    else:
        json_response = {"check":"INJECTION", "class": predicted_class, "lang": language, "blocklist": regex_check}

    return json_response
    
    





    



