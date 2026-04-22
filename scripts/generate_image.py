#!/usr/bin/env python3
"""
GPT Image 2.0 Image Generation Script
Generates images using GPT Image 2.0 via async task workflow.

Usage:
    python generate_image.py --api-key YOUR_KEY --prompt "A serene Japanese garden"
    python generate_image.py --api-key YOUR_KEY --prompt "A cat in space" --size 16:9 --n 2
"""

import argparse
import json
import sys
import time
from typing import Optional

import requests


BASE_URL = "https://www.moodmax.cn/open_api/v2"
POLL_INTERVAL = 3  # seconds
MAX_POLL = 100     # max ~5 minutes


def create_task(
    api_key: str,
    prompt: str,
    size: str = "16:9",
    n: int = 1
) -> dict:
    """Create an image generation task. Returns the task dict with taskId."""
    url = f"{BASE_URL}/create-task"
    payload = {
        "apiKey": api_key,
        "modelCode": "gpt-image-2",
        "prompt": prompt,
        "params": {
            "size": size,
            "n": n
        }
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"Create task failed: {data.get('message')} (code={data.get('code')})")

    return data["data"]


def query_task(api_key: str, task_id: int) -> dict:
    """Query task status by taskId."""
    url = f"{BASE_URL}/query-task"
    payload = {
        "apiKey": api_key,
        "taskId": task_id
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"Query task failed: {data.get('message')} (code={data.get('code')})")

    return data["data"]


def _get_image_url(result: dict) -> Optional[str]:
    """
    Extract image URL from task result.
    Handles both direct url and OSS-transfer fallback.
    """
    output_files = result.get("outputFiles", [])
    if not output_files:
        return None

    first_file = output_files[0]
    url = first_file.get("url")

    # If url is null/empty but the task is completed, it may still be in OSS transfer.
    # The API now falls back to original_url when url is empty, so this should rarely happen.
    if not url and result.get("status") == "completed":
        return None

    return url


def generate_image(
    api_key: str,
    prompt: str,
    size: str = "16:9",
    n: int = 1,
    poll_interval: int = POLL_INTERVAL,
    max_poll: int = MAX_POLL,
    verbose: bool = False
) -> dict:
    """
    Generate an image and wait for completion.

    Returns:
        dict: The final task data with status "completed" and outputFiles.
    """
    # Step 1: Create task
    task = create_task(api_key, prompt, size, n)
    task_id = task["taskId"]

    if verbose:
        print(f"[Task created] taskId={task_id}, status={task['status']}")

    # Step 2: Poll until complete
    for i in range(max_poll):
        time.sleep(poll_interval)
        result = query_task(api_key, task_id)
        status = result["status"]

        if verbose:
            progress = result.get("progress", 0)
            need_transfer = result.get("needTransfer", False)
            transfer_status = result.get("transferStatus", "")
            url = _get_image_url(result)
            print(
                f"[Poll {i+1}/{max_poll}] status={status}, progress={progress}%, "
                f"needTransfer={need_transfer}, transferStatus={transfer_status}, url={'yes' if url else 'no'}"
            )

        if status == "completed":
            # Check if we have a usable URL
            image_url = _get_image_url(result)

            if image_url:
                if verbose:
                    print(f"[Done] Image URL: {image_url}")
                return result
            elif result.get("needTransfer") and result.get("transferStatus") == "pending":
                # OSS transfer is still in progress, continue polling
                if verbose:
                    print(f"[Transfer] Image generated, waiting for OSS transfer...")
                continue
            else:
                raise RuntimeError(
                    f"Image generation completed but no URL available. "
                    f"outputFiles={result.get('outputFiles')}"
                )
        elif status == "failed":
            raise RuntimeError(f"Image generation failed: {result.get('errorMessage', 'Unknown error')}")

    raise TimeoutError(f"Image generation timed out after {max_poll * poll_interval} seconds")


def main():
    parser = argparse.ArgumentParser(description="Generate images with GPT Image 2.0")
    parser.add_argument("--api-key", required=True, help="Your API key from https://www.moodmax.cn")
    parser.add_argument("--prompt", required=True, help="Image description (English works best)")
    parser.add_argument("--size", default="16:9", help="Aspect ratio: 1:1, 16:9, 9:16, 4:3, 3:2, 2:3, 21:9, 9:21")
    parser.add_argument("--n", type=int, default=1, help="Number of images (1-4)")
    parser.add_argument("--verbose", action="store_true", help="Show progress logs")

    args = parser.parse_args()

    try:
        result = generate_image(
            api_key=args.api_key,
            prompt=args.prompt,
            size=args.size,
            n=args.n,
            verbose=args.verbose
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except TimeoutError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
