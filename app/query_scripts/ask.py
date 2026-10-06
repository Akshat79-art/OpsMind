import sys

from retrieve import retrieve
from generation import build_messages, call_llm

def answer(question: str) -> str:

    '''Retrieves context, generates an answer, prints it with sources.'''

    hits = retrieve(question, 5)
    messages, sources = build_messages(question, hits)

    try:
        answer = call_llm(messages)
        print(answer)
        print("\nSources:")
        for n, label in sources.items():
            print(f"[{n}] {label}")
        
    except RuntimeError as err:
        print(f"An internal error occurred: {err}")
        raise SystemExit(1)
    
    return answer

def main():
    if len(sys.argv) < 2:
        print('Usage: python ask.py "your question"')
        raise SystemExit(1)
    answer(" ".join(sys.argv[1:]))


if __name__ == "__main__":
    main()