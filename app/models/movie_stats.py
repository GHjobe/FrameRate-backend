from .base import db

class MovieStats(db.Model):
    __tablename__ = 'movie_stats'
    
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), primary_key=True)
    total_votes = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)
    bayesian_rating = db.Column(db.Float, default=0.0)