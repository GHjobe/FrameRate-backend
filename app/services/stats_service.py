from sqlalchemy import func
from app.models.base import db
from app.models.rating import Rating 
from app.models.movie_stats import MovieStats
from app.services.ranking import bayesian_score

def update_movie_score(movie_id):
    stats = db.session.query(
        func.count(Rating.id).label('votes'),
        func.avg(Rating.rating).label('avg')
    ).filter(
        Rating.movie_id == movie_id,
        Rating.status == 'active'
    ).first()
    
    votes = stats.votes or 0
    avg_rating = float(stats.avg) if stats.avg else 0.0
    
    new_score = bayesian_score(votes, avg_rating)
    
    movie_stat = MovieStats.query.get(movie_id)
    if not movie_stat:
        movie_stat = MovieStats(movie_id=movie_id)
        db.session.add(movie_stat)
        
    movie_stat.total_votes = votes
    movie_stat.average_rating = round(avg_rating, 2)
    movie_stat.bayesian_rating = new_score
    
    db.session.commit()