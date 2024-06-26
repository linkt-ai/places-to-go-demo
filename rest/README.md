# Places To Go Rest API

This is a REST API for the Places to Go Application implemented with Fast API.
The role of this API is to expose the Venue and Social media post resource to
the rest of the applciations services.

## Running the Server

To run the sever, you must first create a virtual environment and install all of
the required dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Once you have an environment created, be sure that you place a copy of `.env` in
the root of the project. We will need this file in order to connect with
external services. Please consult with `.env.example` if you are unsure of the
variables that are required for you to include.

Finally, you can run the application with:

```bash
uvicorn src.rest.app:app --host 127.0.0.1 --port 8000 --reload
```

This will launch the application locally on port 8000, and it will restart the
server everytime a file is changed.

# Resources

Our goal is to provide a clean and sleek REST interface for the Post, Venue,
Itinerary, and Events resources. Additionally, we will provide access to the
Chat endpoint as well, giving clients the ability to create a chat session and
add messages to the chat session.

We will provie the following HTTP endpoints for our resources

## Board Resource

### GET `/board?user_id=<user_id: str>`

Get a user's mood board posts.

### PUT `/board`

Upsert a post to the mood board.

### DELETE `/board`

Remove a post from a user's mood board.

## Venue Resource

### GET `/venue?venue_id=<venue_id: str>`

Get a venue from the database.

## Itinerary Resource

### GET `/itinerary?user_id=<user_id: str>`

Get the itinerary for a user. Optionally declare the events to be returned with
the Itinerary.

### POST `/itinerary`

Create a new itinerary for a user. Will overwrite any current itinerary.

## Event Resource

### POST `/itinerary/event`

Create a new event in the user's current itinerary.

### PUT `/itinerary/event`

Edit the times of an event in the user's itinerary.

### DELETE `/itinerary/event`

Delete an event from the user's itinerary.

## User Resource

### POST `/user`

Create a new user with a username and password

### GET `/user?user_id=<user_id: str>`

Get the users in the database. Optionally, filter by user_id.
