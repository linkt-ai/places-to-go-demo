"""This file defines the graph queries for the Social Media Post resource."""
from typing import List

from .driver import get_driver
from ..models import ClassifiedSocialMediaPost, SocialMediaPost


def get_board(user_id: str) -> List[SocialMediaPost]:
    """Get all posts for a user. This consitutes the mood board for the user.

    Args:
        user_id (str): The user ID for which to get the posts.

    Returns:
        List[SocialMediaPost]: The list of posts for the user.
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (p:Post) WHERE p.userId = $user_id "
            "RETURN p.postUrl AS post_url, "
            "p.authorName AS author_name, "
            "p.videoId AS video_id, "
            "p.embedCode AS embed_code, "
            "p.userId AS user_id, "
            "p.thumbnailUrl AS thumbnail_url",
            user_id=user_id,
        )
        records = result.data()
        return [SocialMediaPost(**record) for record in records]


def create_post(_post: ClassifiedSocialMediaPost) -> int:
    """Create a post in the database.

    Args:
        post (SocialMediaPost): The post to create.

    Returns:
        int: The number of posts created.
    """
    driver = get_driver()
    merges = ""
    weights = ""
    for i, kv_pair in enumerate(_post.classifications.model_dump().items()):
        persona, score = kv_pair
        merges += f"MERGE (p{i}:Persona {{ value : '{persona}' }}) "
        weights += (
            f"MERGE (p)-[r{i}:PERSONA_RELEVANCE]->(p{i}) SET r{i}.weight = {score} "
        )
    relational_cypher = "\n".join([merges, weights])
    with driver.session() as session:
        result = session.run(
            "MERGE (p: Post {userId: $user_id, videoId: $video_id}) "
            "ON CREATE SET p.authorName = $author_name, p.postUrl = $post_url, "
            "p.thumbnailUrl = $thumbnail_url, p.embedCode = $embed_code "
            "ON MATCH SET p.thumbnailUrl = $thumbnail_url, p.embedCode = $embed_code "
            f"{relational_cypher} "
            "RETURN p",
            {
                "user_id": _post.user_id,
                "video_id": _post.video_id,
                "author_name": _post.author_name,
                "post_url": _post.post_url,
                "thumbnail_url": _post.thumbnail_url,
                "embed_code": _post.embed_code,
            },
        )
        summary = result.consume()
        return summary.counters.nodes_created


def delete_post(user_id: str, video_id: str) -> int:
    """Delete a post from the database.

    Args:
        user_id (str): The user ID for which to get the posts.
        video_id (str): The video ID for which to get the posts.

    Returns:
        int: The number of posts deleted.
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (p:Post) WHERE p.userId = $user_id AND p.videoId = $video_id "
            "DETACH DELETE p",
            {
                "user_id": user_id,
                "video_id": video_id,
            },
        )
        summary = result.consume()
        return summary.counters.nodes_deleted
