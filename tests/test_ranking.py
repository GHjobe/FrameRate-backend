from app.services.ranking import bayesian_score

def test_bayesian_scores():
    assert bayesian_score(1, 5.0) == 3.73
    assert bayesian_score(2000, 4.5) == 4.50
    assert bayesian_score(0, 0) == 0.0