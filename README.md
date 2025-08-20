Fantasy Football Pick Grading App

Takes information about a fantasy football pick and sends a reponse to a discord webhook as a certain persona

Requires:
- openai api key
- discord webhooks

Testing:
- create and activate python virtual environment
- install requirements
- start app using `uvicorn app:app --host 0.0.0.0 --port 8000 --reload`
- make request to http://localhost:8000/draft-pick

Sample Request:

{
    "pickNumber": 14,
    "player": "Najee Harris",
    "adp": 28.4,
    "team": "Ryan",
    "persona": "Mel",
    "tone": "roast",
    "leagueType": "redraft"
  }

