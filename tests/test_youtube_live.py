import os
import pytest
from dotenv import load_dotenv
from youtube import get_channel_id

load_dotenv('.env.test')

API_KEY = os.getenv("YOUTUBE_API_KEY")

@pytest.mark.skipif(not API_KEY, reason="YOUTUBE_API_KEY not found in .env.test")
@pytest.mark.parametrize("channel_url, expected_channel_id", [
    ("https://www.youtube.com/@MrBeast/videos", "UCX6OQ3DkcsbYNE6H8uQQuVA"),
    ("https://www.youtube.com/@denis_chuzhoy/videos", "UCCzVNbWZfYpBfyofCCUD_0w"),
])
def test_get_channel_id_live(channel_url, expected_channel_id):
    # This is a live test and requires a valid YOUTUBE_API_KEY
    channel_id = get_channel_id(channel_url, API_KEY)
    assert channel_id == expected_channel_id
