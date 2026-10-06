'''
Generation stage for the query pipeline.
Turns retrieved hits into a grounded prompt and uses OpenRouter for an answer.

- build_messages: assembles the context (each hit labeled [n] with a
  human-readable source) into a system + user prompt, plus a marker→source
  map for citations.
- call_llm: sends the messages to OpenRouter, retrying on rate limits and
  server errors, and returns the assistant's text.

Used by ask.py; requires OPENROUTER_API_KEY and OPENROUTER_MODEL in .env.
'''

import os

import requests
import time

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

def build_messages(question: str, hits: list[dict]) -> tuple[list[dict], dict]:
    '''
    Sets up the prompt for the llm by using the hits provided by retrieve.
    Does so by processing them into a list of messages that is passed to llm.
    '''

    ref_list = []
    sources = {}

    for index, hit in enumerate(hits, 1):
        metadata = hit["metadata"]
        label = metadata.get("title") or metadata.get("source", "unknown")
        page = metadata.get("page")
        if page is not None:
            label = f"{label}, p.{page}"

        ref = f"[{index}] (Source: {label})\n{hit["text"]}"
        ref_list.append(ref)
        sources[str(index)] = label

    context = "\n\n".join(ref_list)
    prompt = f'''User has asked a question that you need to answer. You are provided with the context.
    Answer using only the context given. Cite sources as [n]. If the context doesn't cover the question, say you don't have enough information.
    Do not create answers from sources out of context.'''
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user",   "content": f"Question: {question}\n\n{context}"},
    ]
    
    return messages, sources


def call_llm(messages: list[dict]) -> str:
    '''
    Sends the chat messages to OpenRouter and returns the assistant's text.
    Retries with exponential backoff on rate limits (429) and server errors.
    '''

    apiKey = os.getenv("OPENROUTER_API_KEY")
    backoff_time = 1.0      # 1s, 2s, 4s
    max_attempts = 3

    url="https://openrouter.ai/api/v1/chat/completions"
    headers={
        "Authorization": f"Bearer {apiKey}",
        "Content-Type": "application/json",
    }
    free_models = [
        "dots-studio/dots-3-note-preview:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "thinkingmachines/inkling:free",
        ]
    payload = {"model": free_models[0], "messages": messages}

    last_error = None

    for attempt in range(max_attempts):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
        except requests.RequestException as exc:
            last_error = exc
        else:
            sc = response.status_code

            if sc == 200:
                data = response.json()

                # If LLM responds with an error
                if 'error' in data:
                    error = data['error']
                    err_msg = error['message']
                    print("LLM returned with following error:")
                    print(error)
                    sc = error['code']
                    if sc == 429 or (sc > 499 and sc < 600):
                        last_error = f"HTTP {sc}: {err_msg[:200]}"
                    else:
                        raise RuntimeError(f"{err_msg}")

                # If LLM responds with an answer
                else:
                    # If LLM has choices in the json
                    if 'choices' in data:
                        return data['choices'][0]['message']['content']
                    else:
                        raise RuntimeError(f"Unexpected response: {data}")
            
            if sc in (429, 500, 502, 503, 504):
                last_error = f"HTTP {sc}: {response.text[:200]}"
            else:
                print("Following error occured:")
                print(response.text[:300])
                response.raise_for_status()

        if attempt < max_attempts - 1:
            time.sleep(backoff_time * (2 ** attempt))

    raise RuntimeError(f"OpenRouter request failed after {max_attempts} attempts: {last_error}")