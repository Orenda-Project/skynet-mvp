"""
Simple test script for full pipeline
"""
import sys
import requests
import json
import time

BASE_URL = "http://localhost:8000"

audio_path = sys.argv[1] if len(sys.argv) > 1 else None
if not audio_path:
    print("Usage: python simple_test.py <audio_file.mp3>")
    sys.exit(1)

print("="*80)
print("SKYNET PIPELINE TEST")
print("="*80)
print(f"Audio: {audio_path}\n")

# Step 1: Create conversation and transcribe in one call
print("Step 1: Upload and create conversation...")
try:
    # First create conversation
    resp = requests.post(
        f"{BASE_URL}/v1/transcription/upload",
        data={"title": "Test Meeting"}
    )
    conv_id = resp.json()["conversation_id"]
    print(f"Conversation created: {conv_id}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Response: {resp.text if 'resp' in locals() else 'No response'}")
    sys.exit(1)

# Step 2: Transcribe
print("\nStep 2: Transcribing audio (may take 10-60 seconds)...")
try:
    with open(audio_path, "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/v1/transcription/transcribe/{conv_id}",
            files={"file": f}
        )
    result = resp.json()
    print(f"Done! Words: {result['word_count']}, Time: {result['processing_time_seconds']:.1f}s")
    print(f"Preview: {result['text'][:150]}...")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

# Step 3: Check cost
print("\nStep 3: Checking synthesis cost...")
try:
    resp = requests.get(f"{BASE_URL}/v1/synthesis/cost-estimate/{conv_id}")
    cost = resp.json()
    print(f"Estimated cost: ${cost['estimated_cost_usd']:.4f}")
except Exception as e:
    print(f"Warning: {e}")

# Step 4: Generate synthesis
print("\nStep 4: Generating synthesis (may take 5-15 seconds)...")
try:
    resp = requests.post(
        f"{BASE_URL}/v1/synthesis/generate/{conv_id}",
        json={}
    )
    syn = resp.json()
    print(f"Done! Tokens: {syn['llm_tokens_used']}, Time: {syn['processing_time_seconds']:.1f}s")
except Exception as e:
    print(f"Error: {e}")
    print(f"Response: {resp.text if 'resp' in locals() else 'No response'}")
    sys.exit(1)

# Display results
print("\n" + "="*80)
print("RESULTS")
print("="*80)

print(f"\nSUMMARY:\n{syn['summary']}")

print(f"\nKEY DECISIONS ({len(syn['key_decisions'])}):")
for i, d in enumerate(syn['key_decisions'], 1):
    print(f"  {i}. {d}")

print(f"\nACTION ITEMS ({len(syn['action_items'])}):")
for i, item in enumerate(syn['action_items'], 1):
    print(f"  {i}. {item['task']}")
    print(f"     Owner: {item.get('owner', 'Not specified')}")

print(f"\nOPEN QUESTIONS ({len(syn['open_questions'])}):")
for i, q in enumerate(syn['open_questions'], 1):
    print(f"  {i}. {q}")

print(f"\nKEY TOPICS ({len(syn['key_topics'])}):")
for i, t in enumerate(syn['key_topics'], 1):
    print(f"  {i}. {t}")

print("\n" + "="*80)
print(f"SUCCESS! Conversation ID: {conv_id}")
print("="*80)
