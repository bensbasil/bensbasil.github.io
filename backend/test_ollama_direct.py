import asyncio
import ollama
import os

async def test_ollama():
    client = ollama.AsyncClient(host="http://127.0.0.1:11434")
    print("Testing Ollama chat...")
    try:
        response = await client.chat(
            model="llama3:latest",
            messages=[{"role": "user", "content": "Say hello"}],
        )
        print(f"Ollama response: {response['message']['content']}")
    except Exception as e:
        print(f"Ollama error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama())
