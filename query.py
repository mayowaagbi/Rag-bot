import os
import sys
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def loadchunks(filepath="chunks.pkl"):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filepath} not found.")
    with open(filepath, "rb") as f:
        chunks = pickle.load(f)
    return chunks


def load_faiss_index(filepath="faiss.index"):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filepath} not found.")
    index = faiss.read_index(filepath)
    return index


def load_model(model_name="all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)
    return model


def query_index(question, index, chunks, model, top_k=5):
    question_embedding = model.encode([question])
    distances, indices = index.search(question_embedding, top_k)
    results = [(chunks[i], distances[0][idx]) for idx, i in enumerate(indices[0])]
    return results


def main():
    try:
        chunks = loadchunks()
        index = load_faiss_index()
        model = load_model()
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

    print("Type 'exit' or 'quit' to end the program.\n")
    while True:
        question = input("Type your question: ").strip()
        if question.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        if not question:
            print("Please enter a question.")
            continue
        results = query_index(question, index, chunks, model, top_k=5)
        print("\n=== TOP CHUNKS ===")
        for i, (chunk, dist) in enumerate(results):
            print(f"{i}, (Distance: {dist:.4f})\n{chunk}\n{'-'*40}")
        print("\n=== END OF CHUNKS ===\n")

        top_chunks_text = "\n\n".join([chunk for chunk, _ in results])
        prompt = f"""Context:\n{top_chunks_text}\n\nQuestion: {question}\nAnswer:"""

        try:
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful and concise assistant. Answer the user's question based only on the provided context. "
                            "If the context does not contain relevant information, clearly say so—but still attempt to provide a useful answer from your general knowledge make it extensive."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                model="llama3-70b-8192",
            )
            answer = response.choices[0].message.content
            print(f"\n=== LLM RESPONSE ===\n{answer}\n")
        except Exception as e:
            print(f"Error during Groq API call: {e}")


if __name__ == "__main__":
    main()
