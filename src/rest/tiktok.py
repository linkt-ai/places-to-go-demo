"""This file defines a basic client for interacting with the TikTok API.

It exposes a single method `read_oembed` which takes a TikTok video URL and returns
the oembed data for the video.
"""
import re
import requests

from pydantic import BaseModel

TIK_TOK_POST_URL = "https://www.tiktok.com/@{author_name}/video/{video_id}"

OEMBED_ENDPOINT = "https://www.tiktok.com/oembed?url={post_url}"


class TikTokClientError(Exception):
    """A custom exception for errors raised by the TikTokClient."""


class TikTokOembedResponse(BaseModel):
    """A simple class to represent the oembed response from TikTok.

    Attributes:
        thumbnail_url (str): The URL for the video thumbnail.
        embed_code (str): The HTML embed code for the video.
        post_url (str): The URL for the TikTok post.
        caption (str): The caption for the TikTok post.
    """

    thumbnail_url: str
    embed_code: str
    post_url: str
    caption: str

    def __init__(self, **kwargs):
        """Initialize the TikTokOembedResponse object.

        After the object is initialized, the `embed_code` attribute will be stripped of
        any <script> tags. This is done because we want to inject the embed code once into
        the HTML of our page, and not have the TikTok embed script run multiple times.
        """
        super().__init__(**kwargs)

        # The TikTok API returns the embed code as a string with <script> tags. We
        # want to strip these tags so that we can embed the video in our own HTML.
        self.embed_code = re.sub("<script.*?>|</script>", "", self.embed_code)


class TikTokClient:  # pylint: disable=too-few-public-methods
    """A simple client for interacting with the TikTok API."""

    @staticmethod
    def get_oembed(author_name: str, video_id: str) -> TikTokOembedResponse:
        """Get the oembed data for a TikTok video.

        Args:
            author_name (str): The author's unique TikTok username.
            video_id (str): The video ID for the TikTok video.

        Returns:
            TikTokOembedResponse: An object representing the oembed response from TikTok.

        Raises:
            TikTokClientError: If there is an error getting the oembed data.
        """

        post_url = TIK_TOK_POST_URL.format(author_name=author_name, video_id=video_id)
        url = OEMBED_ENDPOINT.format(post_url=post_url)

        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            raise TikTokClientError("Error getting oembed data")

        data = response.json()
        result = TikTokOembedResponse(
            post_url=post_url,
            embed_code=data.get("html"),
            thumbnail_url=data.get("thumbnail_url"),
            caption=data.get("title"),
        )
        return result
