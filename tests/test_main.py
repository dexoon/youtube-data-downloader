import pytest
from youtube import extract_identifier, extract_links, get_brand_from_url


def test_extract_identifier():
    assert extract_identifier('https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw') == 'UC-lHJZR3Gqxm24_Vd_AJ5Yw'
    assert extract_identifier('https://www.youtube.com/user/someuser') == {'type': 'user', 'id': 'someuser'}
    assert extract_identifier('https://www.youtube.com/c/somechannel') == {'type': 'custom', 'id': 'somechannel'}
    assert extract_identifier('https://www.youtube.com/@somehandle') == {'type': 'handle', 'id': 'somehandle'}
    with pytest.raises(ValueError):
        extract_identifier('https://www.google.com')

def test_extract_links():
    description = "Check out this link: https://www.example.com and this one: http://another-example.com/path?query=1"
    assert extract_links(description) == ['https://www.example.com', 'http://another-example.com/path?query=1']
    assert extract_links("No links here") == []

def test_get_brand_from_url():
    assert get_brand_from_url('https://www.example.com/path') == 'www.example.com'
    assert get_brand_from_url('http://another-example.com') == 'another-example.com'
    assert get_brand_from_url('ftp://invalid.com') == None
