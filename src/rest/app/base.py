"""The app.base module defines the basic Fast API application, along with 
some basic configuration settings that will be used elsewhere in the module.
"""
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.responses import JSONResponse

from ..bert import BertClassifier
from ..config import logger, settings


app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, _exc: RequestValidationError):
    """Handle validation exceptions."""
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid request. Please check the documentation."},
    )


logger.info("API is starting up")

# Load environment variables
ENV_LOADED = load_dotenv(".env")
logger.info("Loaded environment variables: %s", ENV_LOADED)
logger.info("Settings: %s", settings)

# Load model
MODEL = BertClassifier(f"{os.getcwd()}/checkpoints/bert-social.model")


class PredictPayload(BaseModel):
    """The request model for a POST request to the Predict resource."""

    text: str


# Inference endpoint used by the NextJS Application
@app.post("/predict")
async def predict(item: PredictPayload):
    """Predict the personas for a given text."""
    prediction = MODEL.classify(item.text)
    return JSONResponse(content=prediction)
