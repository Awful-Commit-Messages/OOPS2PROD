# OOPS2PROD

What if every NPC in a game was powered by their own AI agent with secrets, goals, and limited knowledge? We built it. The story writes itself.

## Starting the Server with Docker Compose (RECOMMENDED)

1. Create a `.env` file with `ANTHROPIC_API_KEY=` followed by your API key (no quotes)
2. `docker compose up`
3. Open `localhost:8000` in your browser

## Starting Server without Docker (NOT RECOMMENDED)
`uvicorn backend.main:app --reload`

## Our Team

- Adrien Abbey
- David Castro
- Rob Pierce
