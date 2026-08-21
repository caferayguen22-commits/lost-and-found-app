import os
from openai import OpenAI
from dotenv import load_dotenv

# .env Datei laden
load_dotenv()

# OpenAI Client initialisieren (holt sich den Key automatisch aus der .env)
client = OpenAI()

try:
    print("Verbindung zu OpenAI wird aufgebaut...")

    # Ein einfacher Test-Request an GPT
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Kostengünstiges und schnelles Modell
        messages=[
            {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
            {"role": "user", "content": "Sag mir in einem kurzen Satz, dass unsere Verbindung steht!"}
        ]
    )

    # Antwort ausgeben
    print("\n--- Antwort von OpenAI ---")
    print(response.choices[0].message.content)
    print("--------------------------")
    print("\nPerfekt! Dein API-Key funktioniert einwandfrei. 🎉")

except Exception as e:
    print(f"\nFehler beim Verbindungsaufbau: {e}")