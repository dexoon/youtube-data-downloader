import json
import logging
import pandas as pd
from youtube import extract_links
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor


def get_brand_from_description(description, openrouter_api_key=None, openrouter_model=None):
    if not openrouter_api_key or not openrouter_model:
        return {"url": "", "brand": ""}
    """Extract brand from video description using OpenRouter API."""
    prompt = f"""
Извлеки из текста рекламную ссылку и бренд. Ответь только в виде валидного JSON-словаря с ключами "url" и "brand".
Текст:
{description}
"""
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key
        )
        response = client.chat.completions.create(
            model=openrouter_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.0
        )
        logging.info(f"OpenRouter response: {response}")
        if  response.choices[0].message.content is None:
            logging.error("Empty response from OpenRouter")
            return {"url": "", "brand": ""}
        content = response.choices[0].message.content.strip()
        info = json.loads(content[content.find('{'):content.rfind('}')+1])
        if isinstance(info, dict) and 'url' in info and 'brand' in info:
            return info
    except Exception as e:
        logging.error(f"Error extracting brand: {str(e)}")
    # Fallback to regex extraction
    links = extract_links(description)
    return {"url": links[0] if links else "", "brand": ""}

def process_video_descriptions(
    descriptions, openrouter_api_key=None, openrouter_model=None, max_workers=8
):
    def process_one(desc):
        links = extract_links(desc['description'])
        text = desc['description']
        brand_info = get_brand_from_description(
            text, openrouter_api_key=openrouter_api_key, openrouter_model=openrouter_model
        )
        if links:
            return {
                'video_url': desc['url'],
                'title': desc['title'],
                'descriptions': desc['description'],
                'brand': brand_info.get('brand', ''),
                'link': brand_info.get('url', '')
            }
        return None

    # Use ThreadPoolExecutor for parallel I/O
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_one, descriptions))
    # Filter out None results
    data = [r for r in results if r]
    return pd.DataFrame(data) if data else None