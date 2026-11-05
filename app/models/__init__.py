"""Every model must be imported here, otherwise `flask db migrate` will not see its table.
To add a table: create a file in this folder, import it below, then run
`flask db migrate -m "describe the change"` and `flask db upgrade`."""

from .movie import Movie
from .preferences import UserPreferences
from .rating import Rating
from .review import Review
from .user import User
from .watchlist import WatchlistItem
from .movie_stats import MovieStats
__all__ = ["Movie", "Rating", "Review", "User", "UserPreferences", "WatchlistItem", "MovieStats"]