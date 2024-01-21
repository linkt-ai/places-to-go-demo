"""This file defines the model for a Social Media Post.

Currently, TikTok is the only platform for which social media posts are supported. The
social media posts are stored in the Neo4J database. We use there standard 
database driver to access the database.
"""
import re

from pydantic import BaseModel


class SocialMediaPost(BaseModel):
    """This class defines the model for a Social Media Post.

    Attributes:
        post_url (str): The URL for the post.
        author_name (str): The name of the author of the post.
        video_id (str): The ID of the video for the post.
        embed_code (str): The embed code for the video.
        user_id (str): The ID of the user who posted the video.
        thumbnail_url (str): The URL for the thumbnail of the video.
    """

    post_url: str
    author_name: str
    video_id: str
    embed_code: str
    user_id: str
    thumbnail_url: str


class SocialMediaPostPersonas(BaseModel):
    """This class defines the model classifications for a social media post.

    Attributes:
        social_butterfly (float): The score for the social butterfly persona.
        culinary_explorer (float): The score for the culinary explorer persona.
        beauty_fashion_aficionado (float): The score for the beauty and fashion aficionado persona.
        family_oriented_individual (float): The score for the family oriented individual persona.
        art_culture_enthusiast (float): The score for the art and culture enthusiast persona.
        wellness_self_care_advocate (float): The score for the wellness and self care advocate persona.
        adventurer_explorer (float): The score for the adventurer and explorer persona.
        eco_conscious_consumer (float): The score for the eco conscious consumer persona.
    """

    social_butterfly: float
    culinary_explorer: float
    beauty_fashion_aficionado: float
    family_oriented_individual: float
    art_culture_enthusiast: float
    wellness_self_care_advocate: float
    adventurer_explorer: float
    eco_conscious_consumer: float

    def __init__(self, convert: bool = True, **kwargs):
        """Override the constructor to convert the keys from camel case to snake case.

        Kwargs:
            convert (bool): Whether to convert the keys from camel case to snake case.
            kwargs: The keyword arguments to pass to the parent constructor.
        """

        # If we need to convert the keys, convert them.
        if convert:
            kwargs = {self._camel_to_snake(k): v for k, v in kwargs.items()}

        # Create the object.
        super().__init__(**kwargs)

    @staticmethod
    def _camel_to_snake(name):
        """Convert a string from camel case to snake case."""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class ClassifiedSocialMediaPost(SocialMediaPost):
    """This class defines the model for a classified social media post.

    Attributes:
        post_url (str): The URL for the post.
        author_name (str): The name of the author of the post.
        video_id (str): The ID of the video for the post.
        embed_code (str): The embed code for the video.
        user_id (str): The ID of the user who posted the video.
        thumbnail_url (str): The URL for the thumbnail of the video.
        classifications (SocialMediaPostPersonas): The classifications for the post.

    Properties:
        post (SocialMediaPost): The social media post without the classifications.
    """

    classifications: SocialMediaPostPersonas

    @property
    def post(self):
        """Return the social media post without the classifications."""
        return SocialMediaPost(
            post_url=self.post_url,
            author_name=self.author_name,
            video_id=self.video_id,
            embed_code=self.embed_code,
            user_id=self.user_id,
            thumbnail_url=self.thumbnail_url,
        )
