# tools/parser.py
# Sends each comment/message to Gemini and extracts planned and actual hours.

import json
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_INSTRUCTION = """
You extract planned hours and actual hours from GitHub commit or comment messages.
Engineers log their time in various formats.

Rules:
- Extract BOTH planned hours and actual hours if mentioned
- If only one is mentioned, return null for the other
- Convert days to hours (1 day = 8 hours, half day = 4 hours)
- If a number refers to a PR number, issue number, file count,
  line count, or version number — return null for that value
- Never guess. Only return a number if certain it represents time spent
- Ignore everything after a newline — only read the first line

Always return valid JSON in exactly this format, nothing else:
{"planned": <number or null>, "actual": <number or null>}

Examples:
"Efforts: 10h"
    → {"planned": null, "actual": 10.0}

"Effort - 1 day"
    → {"planned": null, "actual": 8.0}

"BLE Log [spent : 1 day]"
    → {"planned": null, "actual": 8.0}

"Auth module | actual: 3.5h | planned: 4h"
    → {"planned": 4.0, "actual": 3.5}

"Orders pagination (#17)"
    → {"planned": null, "actual": null}

"Mocked the STM OTP write and read operations"
    → {"planned": null, "actual": null}
"""


def extract_hours(message: str) -> dict:
    """
    Takes a commit message or PR comment string.
    Returns {"planned": float|None, "actual": float|None}
    """
    if not message or not message.strip():
        return {"planned": None, "actual": None}

    # Only send the first line
    first_line = message.split("\n")[0].strip()

    try:
        time.sleep(12)  # stay under free tier limit (5 requests/min)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=first_line,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
            )
        )

        raw = response.text.strip()

        # Strip markdown fences if Gemini adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)

        planned = result.get("planned")
        actual  = result.get("actual")

        planned = float(planned) if planned is not None else None
        actual  = float(actual)  if actual  is not None else None

        return {"planned": planned, "actual": actual}

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"  ⚠ Parser error on: '{first_line[:50]}' → {e}")
        return {"planned": None, "actual": None}

def extract_hours_from_comment(comment_body: str) -> dict:
    """
    Handles multi-entry comments where
    one comment has multiple date sections each with effort logged.

    Sums ALL hours found across the entire comment.
    Returns {"planned": float|None, "actual": float|None}
    """
    if not comment_body or not comment_body.strip():
        return {"planned": None, "actual": None}

    try:
        time.sleep(12)

        prompt = f"""
Read this entire GitHub comment. It may contain multiple date sections,
each with effort logged. Sum ALL hours mentioned across the whole comment.

Comment:
{comment_body}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
            )
        )

        raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)

        planned = result.get("planned")
        actual  = result.get("actual")

        planned = float(planned) if planned is not None else None
        actual  = float(actual)  if actual  is not None else None

        return {"planned": planned, "actual": actual}

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"  ⚠ Parser error on comment → {e}")
        return {"planned": None, "actual": None}
    
if __name__ == "__main__":
    test_messages = [
        # Format 1 — hariprasath style
        "Efforts: 10h",
        "Efforts: 3.5h",

        # Format 2 — naveenkumar style
        "Effort - 1 day",
        "Effort - 2 days",

        # Format 3 — prathaban style
        "BLE Log [spent : 1 day]",
        "Auth module [spent : 3h]",

        # Edge cases
        "Effort - half day",
        "Efforts: 0.5h",

        # Should return null
        "Mocked the STM OTP write and read operations",
        "Fix retry logic for order webhook",
    ]

    print("Testing parser.py...\n")
    for msg in test_messages:
        result = extract_hours(msg)
        print(f"  Message : {msg}")
        print(f"  Result  : planned={result['plannexd']}  actual={result['actual']}")
        print()