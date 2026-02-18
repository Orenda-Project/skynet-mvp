"""
Test script for full pipeline: Audio → Transcript → Synthesis
Run this with: python test_full_pipeline.py path/to/your/audio.mp3
"""

import sys
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_pipeline(audio_file_path: str):
    """Test the complete pipeline with an audio file."""

    print("=" * 80)
    print("SKYNET FULL PIPELINE TEST")
    print("=" * 80)
    print(f"\nAudio file: {audio_file_path}\n")

    # Step 1: Create conversation
    print("STEP 1: Creating conversation...")
    print("-" * 80)
    try:
        response = requests.post(
            f"{BASE_URL}/v1/transcription/upload",
            data={"title": "Test Meeting - Full Pipeline"}
        )
        response.raise_for_status()
        conversation = response.json()
        conversation_id = conversation["conversation_id"]
        print(f"✓ Conversation created: {conversation_id}")
        print(f"  Status: {conversation['status']}")
    except Exception as e:
        print(f"✗ Failed to create conversation: {e}")
        return

    # Step 2: Transcribe audio
    print("\nSTEP 2: Transcribing audio...")
    print("-" * 80)
    print("⏳ This may take 10-60 seconds depending on audio length...")
    try:
        with open(audio_file_path, "rb") as audio_file:
            response = requests.post(
                f"{BASE_URL}/v1/transcription/transcribe/{conversation_id}",
                files={"file": audio_file}
            )
            response.raise_for_status()
            transcription = response.json()

        print(f"✓ Transcription completed!")
        print(f"  Provider: {transcription['provider']}")
        print(f"  Word count: {transcription['word_count']}")
        print(f"  Processing time: {transcription['processing_time_seconds']:.1f}s")
        print(f"  Language: {transcription['language']}")
        print(f"\n  Transcript preview:")
        print(f"  {transcription['text'][:200]}...")
    except Exception as e:
        print(f"✗ Failed to transcribe: {e}")
        return

    # Step 3: Check synthesis cost
    print("\nSTEP 3: Checking synthesis cost...")
    print("-" * 80)
    try:
        response = requests.get(
            f"{BASE_URL}/v1/synthesis/cost-estimate/{conversation_id}"
        )
        response.raise_for_status()
        cost = response.json()
        print(f"✓ Cost estimate:")
        print(f"  Transcript words: {cost['transcript_word_count']}")
        print(f"  Estimated cost: ${cost['estimated_cost_usd']:.4f}")
        print(f"  Model: {cost['model']}")
    except Exception as e:
        print(f"✗ Failed to estimate cost: {e}")
        # Continue anyway

    # Step 4: Generate synthesis
    print("\nSTEP 4: Generating synthesis...")
    print("-" * 80)
    print("⏳ This may take 5-15 seconds...")
    try:
        response = requests.post(
            f"{BASE_URL}/v1/synthesis/generate/{conversation_id}",
            json={"force_regenerate": False}
        )
        response.raise_for_status()
        synthesis = response.json()

        print(f"✓ Synthesis completed!")
        print(f"  Model: {synthesis['llm_model']}")
        print(f"  Tokens used: {synthesis['llm_tokens_used']}")
        print(f"  Processing time: {synthesis['processing_time_seconds']:.1f}s")
    except Exception as e:
        print(f"✗ Failed to generate synthesis: {e}")
        return

    # Step 5: Display results
    print("\n" + "=" * 80)
    print("SYNTHESIS RESULTS")
    print("=" * 80)

    print(f"\n📝 SUMMARY:")
    print(f"   {synthesis['summary']}")

    print(f"\n✅ KEY DECISIONS ({len(synthesis['key_decisions'])}):")
    if synthesis['key_decisions']:
        for i, decision in enumerate(synthesis['key_decisions'], 1):
            print(f"   {i}. {decision}")
    else:
        print("   (No decisions identified)")

    print(f"\n📋 ACTION ITEMS ({len(synthesis['action_items'])}):")
    if synthesis['action_items']:
        for i, item in enumerate(synthesis['action_items'], 1):
            owner = item.get('owner') or 'Not specified'
            due = item.get('due_date') or 'Not specified'
            print(f"   {i}. {item['task']}")
            print(f"      Owner: {owner} | Due: {due}")
    else:
        print("   (No action items identified)")

    print(f"\n❓ OPEN QUESTIONS ({len(synthesis['open_questions'])}):")
    if synthesis['open_questions']:
        for i, question in enumerate(synthesis['open_questions'], 1):
            print(f"   {i}. {question}")
    else:
        print("   (No open questions)")

    print(f"\n🏷️  KEY TOPICS ({len(synthesis['key_topics'])}):")
    if synthesis['key_topics']:
        for i, topic in enumerate(synthesis['key_topics'], 1):
            print(f"   {i}. {topic}")
    else:
        print("   (No topics identified)")

    # Step 6: Verify cached retrieval
    print("\n" + "=" * 80)
    print("STEP 5: Testing cached retrieval...")
    print("-" * 80)
    try:
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/v1/synthesis/{conversation_id}"
        )
        response.raise_for_status()
        cached = response.json()
        elapsed = time.time() - start

        print(f"✓ Retrieved cached synthesis in {elapsed*1000:.0f}ms")
        print(f"  Created at: {cached['created_at']}")
        print(f"  Synthesis ID: {cached['synthesis_id']}")
    except Exception as e:
        print(f"✗ Failed to retrieve cached synthesis: {e}")

    print("\n" + "=" * 80)
    print("✅ FULL PIPELINE TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print(f"\nConversation ID: {conversation_id}")
    print(f"You can retrieve this synthesis anytime with:")
    print(f"  GET {BASE_URL}/v1/synthesis/{conversation_id}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_full_pipeline.py <path_to_audio.mp3>")
        print("\nExample:")
        print('  python test_full_pipeline.py "C:\\Users\\DELL\\Downloads\\meeting.mp3"')
        print()
        sys.exit(1)

    audio_path = sys.argv[1]

    # Check if file exists
    import os
    if not os.path.exists(audio_path):
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("Error: API server is not healthy")
            print("Please start it with: python -m src.main")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API server at http://localhost:8000")
        print("Please start it with: python -m src.main")
        sys.exit(1)

    test_pipeline(audio_path)
