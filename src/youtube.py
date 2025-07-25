import re
import logging
from typing import List, Dict, Union, Optional
from googleapiclient.discovery import build
from googleapiclient.discovery import Resource


def extract_identifier(channel_url: str) -> Union[str, Dict[str, str]]:
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

def get_channel_id(channel_url: str, api_key: str) -> str:
    logging.info(f"Getting channel ID for URL: {channel_url}")
    youtube: Resource = build('youtube', 'v3', developerKey=api_key)
    info = extract_identifier(channel_url)
    if isinstance(info, str):
        logging.info(f"Channel ID found directly: {info}")
        return info
    if isinstance(info, dict) and info['type'] == 'handle':
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
def get_uploads_playlist_id(youtube: Resource, channel_id: str) -> str:
    response = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()
    logging.info(f"Getting uploads playlist ID for channel ID: {channel_id}")
    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def get_last_video_ids(youtube: Resource, playlist_id: str, max_results: int = 20) -> List[str]:
    video_ids: List[str] = []
    next_page_token: Optional[str] = None
    while len(video_ids) < max_results:
        remaining: int = max_results - len(video_ids)
        req = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=min(50, remaining),
            pageToken=next_page_token
        )
        res = req.execute()
        logging.info(f"Fetching video IDs from playlist: {playlist_id}, found: {len(res.get('items', []))}, remaining: {remaining}")
        for item in res["items"]:
            video_ids.append(item["snippet"]["resourceId"]["videoId"])
            if len(video_ids) >= max_results:
                break
        next_page_token = res.get("nextPageToken")
        if not next_page_token:
            break
    logging.info(f"Total video IDs fetched: {len(video_ids)}")
    return video_ids

def get_last_videos(youtube: Resource, channel_id: str, n: int = 10) -> List[str]:
    logging.info(f"Getting last {n} videos for channel ID: {channel_id}")
    req = youtube.search().list(
        part='id',
        channelId=channel_id,
        maxResults=n,
        order='date',
        type='video'
    )
    res = req.execute()
    video_ids: List[str] = [item['id']['videoId'] for item in res['items']]
    logging.info(f"Found {len(video_ids)} video IDs.")
    return video_ids

def get_video_descriptions(youtube: Resource, video_ids: List[str]) -> List[Dict[str, str]]:
    logging.info(f"Getting descriptions for {len(video_ids)} videos.")
    descriptions: List[Dict[str, str]] = []
    
    # Process video IDs in chunks of 50
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        req = youtube.videos().list(
            part='snippet',
            id=','.join(chunk)
        )
        res = req.execute()
        for item in res['items']:
            if  item['snippet']['description']:
                descriptions.append({
                'video_id': item['id'],
                'title': item['snippet']['title'],
                'url': f"https://www.youtube.com/watch?v={item['id']}",
                'description': item['snippet']['description']
            })
    
    logging.info(f"Retrieved {len(descriptions)} descriptions.")
    return descriptions

def extract_links(description: str) -> List[str]:
    return re.findall(r'https?://\S+', description)

def get_brand_from_url(url: str) -> Optional[str]:
    domain = re.findall(r'https?://([^/\s]+)', url)
    if domain:
        return domain[0]
    return None
