"""This is the script to run the FastAPI app."""
import os

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import JSONResponse

from .social import BertClassifier

app = FastAPI()

# Load model
MODEL = BertClassifier(f"{os.getcwd()}/checkpoints/bert-social.model")


class Item(BaseModel):
    text: str


# Inference endpoint used by the NextJS Application
@app.post("/predict")
async def predict(item: Item):
    prediction = MODEL.classify(item.text)
    return JSONResponse(content=prediction)


# Social Media Post Resource.


@app.get("/post")
async def get_post():
    """Get a post."""
    return {"post": "Hello World!"}


@app.post("/post")
async def create_post():
    """Create a post."""
    return {"post": "Hello World!"}


@app.put("/post")
async def update_post():
    """Update a post."""
    return {"post": "Hello World!"}


@app.delete("/post")
async def delete_post():
    """Delete a post."""
    return {"post": "Hello World!"}
