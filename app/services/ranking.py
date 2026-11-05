def bayesian_score(v, R, C=3.6, m=10):
    if v == 0:
        return 0.0
    score = ((R * v) + (C * m)) / (v + m)
    return round(score, 2)