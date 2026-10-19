# jubilant-tribble
AI multi agent ChatBot.

## Requirements

- [Node.js](https://nodejs.org/) 20.19+ or 22.12+
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

## Getting started

Install uv:

```sh
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal so `uv` is on your PATH, then install Python and the backend dependencies:

```sh
cd backend
uv sync
```

Add `GEMINI_API_KEY=your-key` to a `.env` file in the repo root.

Create the knowledge base:

```sh
cd backend
uv run python -m app.build_species_information
```

Start the backend:

```sh
cd backend
uv run fastapi dev app/main.py
```

Start the frontend:

```sh
cd frontend
npm install
npm run dev
```
