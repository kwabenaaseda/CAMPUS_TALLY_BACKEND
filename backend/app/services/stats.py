from app.repositories import stats as stats_repo
from sqlalchemy.orm import Session

def get_formatted_stats(db: Session, election_id: str):
    raw_stats = stats_repo.get_election_stats(db, election_id)
    
    # Transform list of tuples into a clean dictionary
    # Example output: {"cand_1": 150, "cand_2": 85}
    return {str(row.candidate_index): row.total_votes for row in raw_stats}