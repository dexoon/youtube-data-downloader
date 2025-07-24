import re
import logging
from urllib import response
from googleapiclient.discovery import build


def extract_identifier(channel_url):
    logging.info(f"Extracting identifier from URL: {channel_url}")
    m = re.search(r'youtube\.com/(channel|c|user|@[\w\-\.]+|@[\w\-]+)', channel_url)
    if not m:
        logging.error(f"Could not parse YouTube channel URL: {channel_url}")
        raise ValueError("Can't parse YouTube channel url")
    if '/channel/' in channel_url:
        return channel_url.split('/channel/')[1].split('/')[0]
    if '/user/' in channel_url:
        return {'type': 'user', 'id': channel_url.split('/user/')[1].split('/')[0]}
    if '/c/' in channel_url:
        return {'type': 'custom', 'id': channel_url.split('/c/')[1].split('/')[0]}
    if '/@' in channel_url:
        return {'type': 'handle', 'id': channel_url.split('/@')[1].split('/')[0]}
    logging.error(f"Unknown channel URL format: {channel_url}")
    raise ValueError("Unknown channel url format")

def get_channel_id(channel_url, api_key):
    logging.info(f"Getting channel ID for URL: {channel_url}")
    youtube = build('youtube', 'v3', developerKey=api_key)
    info = extract_identifier(channel_url)
    if isinstance(info, str):
        logging.info(f"Channel ID found directly: {info}")
        return info
    if info['type'] == 'handle':
        query = f"@{info['id']}"
    else:
        query = info['id']
    logging.info(f"Searching for channel with query: {query}")
    search_response = youtube.channels().list(
        part='id',
        forHandle=query,
        maxResults=1
    ).execute()
    items = search_response.get('items', [])
    if not items:
        logging.error(f"Could not find channel with query: {query}")
        raise Exception("Can't find channel by query: " + query)
    channel_id = items[0]['id']
    logging.info(f"Found channel ID: {channel_id}")
    return channel_id
    
def get_last_videos(youtube, channel_id, n=10):
    logging.info(f"Getting last {n} videos for channel ID: {channel_id}")
    req = youtube.search().list(
        part='id',
        channelId=channel_id,
        maxResults=n,
        order='date',
        type='video'
    )
    res = req.execute()
    video_ids = [item['id']['videoId'] for item in res['items']]
    logging.info(f"Found {len(video_ids)} video IDs.")
    return video_ids

def get_video_descriptions(youtube, video_ids):
    logging.info(f"Getting descriptions for {len(video_ids)} videos.")
    descriptions = []
    req = youtube.videos().list(
        part='snippet',
        id=','.join(video_ids)
    )
    res = req.execute()
    for item in res['items']:
        descriptions.append({
            'video_id': item['id'],
            'title': item['snippet']['title'],
            'url': f"https://www.youtube.com/watch?v={item['id']}",
            'description': item['snippet']['description']
        })
    logging.info(f"Retrieved {len(descriptions)} descriptions.")
    return descriptions

def extract_links(description):
    return re.findall(r'https?://\S+', description)

def get_brand_from_url(url):
    domain = re.findall(r'https?://([^/\s]+)', url)
    if domain:
        return domain[0]
    return None
