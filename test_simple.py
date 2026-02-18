"""Simple working test"""
import sys
import requests

audio_path = sys.argv[1]
BASE_URL = "http://localhost:8000"

print("="*70)
print("SKYNET TEST")
print("="*70)

# Step 1: Upload and create conversation
print("\n1. Creating conversation...")
resp = requests.post(
    f"{BASE_URL}/v1/transcription/upload",
    data={"title": "Test Meeting"}
)
conv_id = resp.json()["conversation_id"]
print(f"   Created: {conv_id}")

# Step 2: Transcribe
print("\n2. Transcribing (30-60 sec)...")
with open(audio_path, "rb") as f:
    resp = requests.post(
        f"{BASE_URL}/v1/transcription/transcribe/{conv_id}",
        files={"file": f}
    )
trans = resp.json()
print(f"   Words: {trans['word_count']}")
print(f"   Preview: {trans['text'][:100]}...")

# Step 3: Synthesize
print("\n3. Generating synthesis (10-15 sec)...")
resp = requests.post(f"{BASE_URL}/v1/synthesis/generate/{conv_id}", json={})
syn = resp.json()

# Results
print("\n" + "="*70)
print("RESULTS")
print("="*70)
print(f"\nSUMMARY:\n{syn['summary']}\n")
print(f"DECISIONS ({len(syn['key_decisions'])}):")
for d in syn['key_decisions']: print(f"  - {d}")
print(f"\nACTIONS ({len(syn['action_items'])}):")
for a in syn['action_items']: print(f"  - {a['task']} (Owner: {a.get('owner', 'TBD')})")
print(f"\nQUESTIONS ({len(syn['open_questions'])}):")
for q in syn['open_questions']: print(f"  - {q}")
print(f"\nTOPICS: {', '.join(syn['key_topics'])}")
print(f"\n{'='*70}")
print(f"Conversation: {conv_id}")
