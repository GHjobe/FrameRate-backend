# Database schema

Tables created by the first migration. Other tables, such as `movie_stats` for the Bayesian ranking
and the backlog tables (review votes, reports), are added later by their owners with their own migrations.

```mermaid
erDiagram
    users ||--o{ ratings : gives
    users ||--o{ watchlist : keeps
    users ||--o| user_preferences : has
    movies ||--o{ ratings : receives
    movies ||--o{ watchlist : "appears in"
    ratings ||--o| reviews : "may have"

    users {
        int id PK
        string username "unique, ignoring case"
        string email "unique, ignoring case"
        string password_hash
        string role "user | moderator | admin"
        bool email_verified
        bool onboarding_completed
        datetime created_at
    }
    movies {
        int tmdb_id PK
        string title
        int year
        int runtime
        text overview
        string poster_path
        string backdrop_path
        json genres
        datetime fetched_at
    }
    ratings {
        int id PK
        int user_id FK
        int tmdb_id FK
        int score "1 to 5"
        string status "active | quarantined | removed"
        datetime created_at
        datetime updated_at
    }
    reviews {
        int id PK
        int rating_id FK "unique"
        text body
        bool contains_spoiler
        bool is_hidden
        datetime created_at
        datetime updated_at
    }
    watchlist {
        int user_id PK
        int tmdb_id PK
        string status "plan | watched | on_hold | dropped"
        datetime added_at
        datetime updated_at
    }
    user_preferences {
        int user_id PK
        string region
        string language
        bool blur_spoilers
        json genres
        json services
    }
```

## Rules the database enforces

| Rule | How |
|---|---|
| One rating per user per movie | unique `(user_id, tmdb_id)` on `ratings` |
| Score is 1 to 5 | check constraint on `ratings.score` |
| One review per rating, never blank | unique `rating_id`, check on `body` |
| One watchlist entry per user per movie | composite primary key `(user_id, tmdb_id)` |
| Status values are valid | check constraints on `role`, rating `status`, watchlist `status` |
| Same username or email in a different case is a duplicate | unique index on `lower(username)` and `lower(email)` |
| Deleting a user removes their ratings, reviews, watchlist, and preferences | `ON DELETE CASCADE` |
| A movie that has ratings or watchlist entries cannot be deleted | `ON DELETE RESTRICT` |

A movie must be saved in `movies` before anyone can rate it or add it to a watchlist. The rating and
watchlist endpoints should fetch it through the TMDB wrapper first.

## How the frontend's names map

| Frontend | Database |
|---|---|
| movie `id` | `movies.tmdb_id` |
| movie `synopsis` | `movies.overview` |
| watchlist `movieId`, `dateAdded` | `watchlist.tmdb_id`, `added_at` |
| user `emailVerified`, `onboardingCompleted` | `email_verified`, `onboarding_completed` (the API converts the names) |