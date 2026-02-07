# OOPS2PROD

> Shhh.  It's a *secret*.

## Our Team

- Adrien Abbey
- David Castro
- Rob Pierce

## Starting the Server with Docker Compose (RECOMMENDED)

0. Create a `.env` file with `ANTHROPIC_API_KEY=` followed by your API key (no quotes)
1. `docker compose up`
2. Open `localhost:8000` in your browser

## Starting Server without Docker (NOT RECOMMENDED)
`uvicorn backend.main:app --reload`
