import pandas as pd
from data_processing import process_video_descriptions

def test_process_video_descriptions_with_links():
    descriptions = [
        {
            'url': 'https://video.one',
            'title': 'Video One',
            'description': 'Check out https://example.com'
        },
        {
            'url': 'https://video.two',
            'title': 'Video Two',
            'description': 'Another link http://another.com/page and one more https://www.google.com'
        }
    ]
    df = process_video_descriptions(descriptions)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert df.iloc[0]['video_url'] == 'https://video.one'
    assert df.iloc[1]['brands'] == 'another.com, www.google.com'

def test_process_video_descriptions_no_links():
    descriptions = [
        {
            'url': 'https://video.one',
            'title': 'Video One',
            'description': 'No links here'
        }
    ]
    df = process_video_descriptions(descriptions)
    assert df is None

def test_process_video_descriptions_empty_input():
    descriptions = []
    df = process_video_descriptions(descriptions)
    assert df is None
