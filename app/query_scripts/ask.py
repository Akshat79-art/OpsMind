import sys

from retrieve import retrieve
from generation import augment_prompt, generate_answer

def answer(question: str) -> str:

    '''Retrieves context, generates an answer, prints it with sources.'''

    hits = retrieve(question, 5)
    messages, sources = augment_prompt(question, hits)

    try:
        answer = generate_answer(messages)
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