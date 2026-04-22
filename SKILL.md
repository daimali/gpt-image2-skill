---
name: gpt-image-2-generator
description: |
  Generate high-quality images using GPT Image 2.0 based on natural language descriptions.
  Make sure to use this skill whenever the user wants to create images, generate pictures,
  design posters, make avatars, create wallpapers, draw illustrations, produce artwork,
  or create any kind of visual content, even if they don't explicitly say "generate an image".
  Also use when the user mentions creating banners, book covers, product photos,
  social media graphics, concept art, or any visual design task.
---

# GPT Image 2.0 Image Generation

## When to use

Use this skill when the user wants to:
- Create images, pictures, photos, or artwork
- Design posters, banners, covers, or social media graphics
- Generate avatars, profile pictures, or icons
- Create wallpapers (desktop or mobile)
- Produce illustrations, concept art, or drawings
- Make product photos or mockups
- Generate any kind of visual content from text description

## Prerequisites

- **API Key**: The user must have an API Key from the platform.
  - If the user has not provided an API key, ask them to provide one.
  - Tell them they can get an API key at **https://www.moodmax.cn** → top-right corner → **Settings**.
- **Credits**: Each generation consumes credits; failed generations do not deduct credits

## How it works

Image generation is an **asynchronous** process with two steps:

1. **Create task** -> returns a `taskId`
2. **Poll for result** -> returns image URL when complete

```
Step 1: POST /open_api/v2/create-task -> taskId
Step 2: Wait 3-5 seconds
Step 3: POST /open_api/v2/query-task -> status
         ├─ "completed" -> get image URL
         ├─ "processing" -> wait 3s, back to Step 3
         └─ "failed" -> report error
```

Polling: every 3 seconds, up to 100 times (~5 min timeout).

## Tool: Generate Image

**Execute the bundled Python script** `scripts/generate_image.py` directly:

```bash
python scripts/generate_image.py \
  --api-key "YOUR_API_KEY" \
  --prompt "A serene Japanese garden with cherry blossoms, watercolor style" \
  --size 16:9 \
  --n 1 \
  --verbose
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--api-key` | string | Yes | API key |
| `--prompt` | string | Yes | Image description (English works best) |
| `--size` | string | No | Aspect ratio. Default: `16:9` |
| `--n` | integer | No | Number of images. Default: `1`, Max: `4` |
| `--verbose` | boolean | No | Show progress logs |

**Size options**:

| Ratio | Best for |
|-------|----------|
| 1:1 | Avatars, icons, social media |
| 16:9 | Landscape posters, desktop wallpapers |
| 9:16 | Mobile wallpapers, portrait posters |
| 4:3 | Product photos, PPT images |
| 3:2 | Photography, landscapes |
| 2:3 | Book covers, portrait illustrations |
| 21:9 | Ultra-wide wallpapers |
| 9:21 | Ultra-tall posters |

**Response**:
```json
{
  "taskId": 12345,
  "status": "completed",
  "progress": 100,
  "outputFiles": [
    {
      "url": "https://cdn.example.com/images/abc123.jpg",
      "type": "image/jpeg"
    }
  ]
}
```

**Or use the Python functions directly** in your code:

```python
from scripts.generate_image import generate_image

result = generate_image(
    api_key="YOUR_API_KEY",
    prompt="A serene mountain lake at sunset, photorealistic",
    size="16:9",
    n=1,
    verbose=True
)
print(result["outputFiles"][0]["url"])
```

## API Reference (for custom integration)

### Create task

```python
from scripts.generate_image import create_task

task = create_task(api_key, prompt, size="1:1", n=1)
# Returns: {"taskId": 12345, "taskCode": "T2025...", "status": "submitted"}
```

### Query task

```python
from scripts.generate_image import query_task

result = query_task(api_key, task_id=12345)
# Returns: {"taskId": 12345, "status": "completed", "outputFiles": [...]}
```

## Prompt writing guide

**Best structure**:
```
[Subject] + [Scene/Environment] + [Lighting] + [Art style] + [Quality level]
```

**Examples**:

- Landscape: `A serene mountain lake at sunset, golden light reflecting on water, surrounded by pine trees and distant snow-capped peaks, photorealistic, 8K quality`
- Portrait: `Portrait of a young Asian woman with long black hair, wearing a white dress, standing in a sunflower field, soft natural lighting, bokeh background, professional photography`
- Product: `A sleek minimalist wireless headphone, matte black finish, placed on a white marble surface, soft studio lighting, product photography, high detail`
- Illustration: `Cute cartoon cat wearing a space suit, floating in space with planets and stars, pastel colors, flat illustration style, children's book illustration`

**Tips**:
- Use **English** for prompts — results are significantly better
- Be specific and detailed
- Include art style keywords (photorealistic, watercolor, flat illustration, anime)

## Error codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Proceed |
| -1 | General error | Check `message` field |
| 401 | Invalid API Key | Verify API key |
| 403 | No permission | Check permissions |
| 404 | Task not found | Verify taskId |
| 429 | Too many requests | Slow down |
| 500 | Server error | Retry later |

## Important notes

- Image generation takes **10-30 seconds**. Always poll — never assume it's ready immediately.
- Image URLs expire after **7 days** — download promptly.
- The user must have an **API Key** configured.
- Failed generations **do not deduct credits**.
- Maximum **4 images** per request.
- Maximum **3 concurrent tasks** per API key.
