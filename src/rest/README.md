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

## Post Resource

### GET `/post?user_id=<user_id: str>`

Get a user's mood board posts.

### POST `/post`

Add a post to a user's mood board.

### PUT `/post`

Update a social media post (typically for thumbnails)

### DELETE `/post`

Remove a post from a user's mood board.

## Venue Resource

### GET `/venue?venue_id=<venue_id: str>`

Get a venue from the database.

## Itinerary Resource

### GET `/itinerary?user_id=<user_id: str>`

Get the itinerary for a user.

### POST `/itinerary`

Create a new itinerary for a user. Will overwrite any current itinerary.

## Event Resource

### GET `/itinerary/event?user_id=<user_id: str>&event_id=<event_id?: str>`

Get the events for a user's itinerary. Optionally filter for a specific event if
only one event is required.

### POST `/itinerary/event`

Create a new event in the user's current itinerary.

### PUT `/itinerary/event`

Edit the times of an event in the user's itinerary.

### DELETE `/itinerary/event`

Delete an event from the user's itinerary.
