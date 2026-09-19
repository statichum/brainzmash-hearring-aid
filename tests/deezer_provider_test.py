"""The Deezer fallback must never guess an artist from its name."""

import pytest

from lidarrmetadata.provider import DeezerProvider


@pytest.mark.parametrize('target,expected', [
    ('https://www.deezer.com/artist/12345', '12345'),
    ('https://www.deezer.com/en/artist/12345/', '12345'),
    ('https://deezer.com/artist/12345?utm_source=musicbrainz', '12345'),
    ('https://evil.example/artist/12345', None),
    ('https://www.deezer.com/album/12345', None),
    ('https://www.deezer.com/artist/12345/extra', None),
])
def test_artist_id_requires_linked_deezer_artist(target, expected):
    assert DeezerProvider.artist_id_from_links([{'target': target}]) == expected


def test_unlinked_artist_has_no_deezer_id():
    assert DeezerProvider.artist_id_from_links([{'target': 'https://example.com/artist/12345'}]) is None


def test_picture_rewritten_to_image_cache():
    provider = DeezerProvider()
    result = provider.image_from_response({
        'picture_big': 'https://cdn-images.dzcdn.net/images/artist/'
        '638e69b9caaf9f9f3f8826febea7b543/500x500-000000-80-0-0.jpg'
    })
    assert result == [{
        'CoverType': 'Poster',
        'Url': 'https://tadb.brainzmash.cc/deezer/images/artist/'
        '638e69b9caaf9f9f3f8826febea7b543/500x500-000000-80-0-0.jpg',
    }]


def test_picture_from_unrecognised_host_is_not_proxied():
    provider = DeezerProvider()
    assert provider.image_from_response({
        'picture_big': 'https://evil.example/images/artist/'
        '638e69b9caaf9f9f3f8826febea7b543/500x500-000000-80-0-0.jpg'
    }) == []


@pytest.mark.asyncio
async def test_unlinked_artist_makes_no_request(monkeypatch):
    provider = DeezerProvider()

    async def unexpected_request(*args, **kwargs):
        raise AssertionError('Deezer was queried without a linked artist ID')

    monkeypatch.setattr(provider, 'get_with_limit', unexpected_request)
    images, _ = await provider.get_linked_artist_images([])
    assert images == []


@pytest.mark.asyncio
async def test_deezer_failure_does_not_break_artist(monkeypatch):
    provider = DeezerProvider()

    async def unavailable(*args, **kwargs):
        raise RuntimeError('upstream unavailable')

    monkeypatch.setattr(provider, 'get_with_limit', unavailable)
    images, _ = await provider.get_linked_artist_images([
        {'target': 'https://www.deezer.com/artist/1343811'}
    ])
    assert images == []
