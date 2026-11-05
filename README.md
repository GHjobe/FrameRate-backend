# FrameRate backend (Flask)

## Run it (Windows Command Prompt)

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Then open http://127.0.0.1:5000/api/health. You should see `"status": "ok"` and `"database": "ok"`.

- `copy .env.example .env` is only needed once. Put your own values in `.env` (it is never committed).
- Run the tests with `pytest` from the `backend` folder.
- The old `backend/app.py` is replaced by `run.py`. The new command is `python run.py`.

## Folder map

```
backend/
  run.py                  starts the server (python run.py)
  .flaskenv               tells the flask command where the app is
  pytest.ini              test settings
  app/
    __init__.py           create_app(): wires everything together
    config.py             settings read from .env
    extensions.py         db and migrate objects, SQLite foreign-key switch
    blueprints/           one file per feature's routes
    utils/                security helpers and validators     (Dev 4)
    services/             ranking and recommendation logic    (Dev 5)
  tests/                  pytest tests
```

The `models/` folder and the `migrations/` folder arrive with API-02.

## Who edits what (keeps merges clean)

| Area | Owner | Files |
|---|---|---|
| App setup, models, auth, TMDB wrapper | Dev 3 | `app/__init__.py`, `config.py`, `extensions.py`, `models/`, `blueprints/auth.py`, `blueprints/movies.py` |
| Security, validation, error handling, logging, preferences | Dev 4 | `app/utils/`, `blueprints/preferences.py` (error-handler and logging files: Dev 4 decides the names) |
| Ranking, ratings, reviews, watchlist | Dev 5 | `app/services/`, `blueprints/ratings.py`, `reviews.py`, `watchlist.py` |

Every blueprint already exists as an empty file, so you add routes without touching `__init__.py`.
Dev 4 only needs to add two lines in `app/__init__.py`, at the comment marked `SEC-02`.