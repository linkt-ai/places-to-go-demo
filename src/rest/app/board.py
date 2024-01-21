"""Board API endpoints."""
from pydantic import BaseModel
from starlette.responses import JSONResponse

from .base import app, MODEL

from ..config import logger
from ..graph import graph_board
from ..models import ClassifiedSocialMediaPost, SocialMediaPostPersonas
from ..tiktok import TikTokClient, TikTokClientError


# REQUEST BODIES


class HTTPMoodBoardPUTRequest(BaseModel):
    """The request model for a PUT request to the Mood Board resource."""

    # The video ID of the video being added
    video_id: str

    # The username of the author of the video
    author_name: str

    # The user to whose mood board the post is added
    user_id: str


class HTTPMoodBoardDELETERequest(BaseModel):
    """The request model for a DELETE request to the Mood Board resource."""

    # The video ID of the video being added
    video_id: str

    # The user to whose mood board the post is added
    user_id: str


@app.get("/board")
async def route__get_boards(user_id: str = None):
    """Get a user's social media mood board.

    Kwargs:
        user_id (str): The user ID for which to get the posts.

    Returns:
        JSONResponse (200): The response for the request.

    Raises:
        JSONResponse (400): If the user ID is not provided.
        JSONResponse (500): If there is an internal server error.
    """
    try:
        # Assert the the user ID is provided.
        if not user_id:
            return JSONResponse(
                status_code=400, content={"detail": "User ID is required"}
            )

        result = graph_board.get_board(user_id)
        json_result = [post.model_dump() for post in result]
        return JSONResponse(status_code=200, content=json_result)
    except Exception as exp:  # pylint: disable=broad-except
        logger.error(exp)
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )


@app.put("/board")
async def route__update_board(payload: HTTPMoodBoardPUTRequest):
    """Upsert a post on the mood board.

    If the post already exists, the post metadata will be udpated via the response
    returned from the `oembed` tiktok endpoint. If the post does not exist, it will
    be created.

    Args:
        payload (HTTPMoodBoardPUTRequest): The payload for the request.

    Returns:
        JSONResponse (200): The response for the request.

    Raises:
        JSONResponse (400): If the TikTok post is invalid.
    """
    try:
        # Setup TikTok client to hit o_embed endpoint for video data
        video_metadata = TikTokClient.get_oembed(payload.author_name, payload.video_id)

        # Run the post caption through the inference model
        prediction = MODEL.classify(video_metadata.caption)

        # Create ClassifiedSocialMediaPost object
        classified_post = ClassifiedSocialMediaPost(
            post_url=video_metadata.post_url,
            author_name=payload.author_name,
            video_id=payload.video_id,
            embed_code=video_metadata.embed_code,
            user_id=payload.user_id,
            thumbnail_url=video_metadata.thumbnail_url,
            classifications=SocialMediaPostPersonas(**prediction),
        )

        # Create a post in the database
        post_created = graph_board.create_post(classified_post)

        # Return the count of posts created by the query (either 0 or 1)
        return JSONResponse(
            {
                "post_created_count": post_created,
                "post": classified_post.post.model_dump(),
            },
            status_code=200,
        )
    except TikTokClientError:
        return JSONResponse(
            {"detail": "The provided TikTok post is invalid."}, status_code=400
        )
    except Exception as exp:  # pylint: disable=broad-except
        logger.error(exp)
        return JSONResponse({"detail": "Internal Server Error"}, status_code=500)


@app.delete("/board")
async def route__delete_board(payload: HTTPMoodBoardDELETERequest):
    """Delete a post.

    Args:
        payload (HTTPMoodBoardDELETERequest): The payload for the request.

    Returns:
        JSONResponse (200): The response for the request.

    Raises:
        JSONResponse (404): If the post is not found.
    """
    try:
        # Delete a post from the database
        post_deleted = graph_board.delete_post(payload.user_id, payload.video_id)

        if post_deleted == 0:
            return JSONResponse(
                status_code=404,
                content={"detail": "Post not found"},
            )
        # Return the count of posts deleted by the query (should be 1, if count is greater
        # than 1 if there are multiple posts with the same video ID for a user -- this would
        # be a bug if this occurs)
        return {"post_deleted_count": post_deleted}
    except Exception as exp:  # pylint: disable=broad-except
        logger.error(exp)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )
