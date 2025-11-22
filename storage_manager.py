import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StorageError(Exception):
    pass

class StorageManager:

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)
        self.results_path: Path = Path(base_path) / 'results'
        self.results_path.mkdir(parents=True, exist_ok=True)
        self.resumes_db = self.results_path / 'resumes_database.json'
        self.opportunities_db = self.results_path / 'opportunities_database.json'
        self.scores_db = self.results_path / 'scores_database.json'
        self.metadata_db = self.results_path / 'metadata_db.json'
        self.initialize_databases()

    def initialize_databases(self):
        if not self.resumes_db.exists():
            self.save_json(self.resumes_db, {
                'resumes': {},
                'next_id': 1
            })

        if not self.opportunities_db.exists():
            self.save_json(self.opportunities_db, {
                'opportunities': {},
                'next_id': 1
            })

        if not self.scores_db.exists():
            self.save_json(self.scores_db, {
                'scores': {},
            })

        if not self.metadata_db.exists():
            self.save_json(self.metadata_db, {
                'last_check': None,
                'total_resumes': 0,
                'total_opportunities': 0,
                'total_scores': 0
            })

    def load_json(self, file_path: Path) -> Dict:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            raise StorageError(f"Failed to load {file_path.name}: {str(e)}") from e

    def save_json(self, file_path: Path, data: Dict) -> None:
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        except Exception as e:
            raise StorageError(f"Failed to save {file_path.name}: {str(e)}") from e

    def register_resume(self, filename: str, file_path: str, text: str) -> int:
        db = self.load_json(self.resumes_db)
        for resume_id, resume_data in db['resumes'].items():
            if resume_data['filename'] == filename:
                logger.info(f"Resume {resume_id} already exists, (ID: {resume_id})")
                return int(resume_id)
        new_id = db['next_id']
        db['resumes'][str(new_id)] = {
            'filename': filename,
            'file_path': str(file_path),
            'text': text,
            'registered_at': datetime.now().isoformat(),
            'email': None,
            'phone': None
        }
        db['next_id'] += 1
        self.save_json(self.resumes_db, db)
        logger.info(f"New Resume {db['next_id']} registered (ID: {new_id})")
        return new_id

    def register_opportunity(self, filename: str, file_path: str, text: str, position: str) -> int:
        db = self.load_json(self.opportunities_db)
        for opp_id, opp_data in db['opportunities'].items():
            if opp_data['filename'] == filename:
                logger.info(f"Opportunity already exists, (ID: {opp_id})")
                return int(opp_id)
        new_id = db['next_id']
        db['opportunities'][str(new_id)] = {
            'filename': filename,
            'file_path': str(file_path),
            'text': text,
            'position': position,
            'registered_at': datetime.now().isoformat(),
        }
        db['next_id'] += 1
        self.save_json(self.opportunities_db, db)
        logger.info(f"Registered new opportunity: {filename} (ID: {new_id})")
        return new_id

    def get_resume(self, resume_id: int) -> Optional[Dict]:
        db = self.load_json(self.resumes_db)
        return db['resumes'].get(str(resume_id))

    def get_opportunity(self, opp_id: int) -> Optional[Dict]:
        db = self.load_json(self.opportunities_db)
        return db['opportunities'].get(str(opp_id))

    def get_all_resumes(self) -> Dict[int,Dict]:
        db = self.load_json(self.resumes_db)
        return {int(k): v for k, v in db['resumes'].items()}

    def get_all_opportunities(self) -> Dict[int, Dict]:
        db = self.load_json(self.opportunities_db)
        return {int(k): v for k, v in db['opportunities'].items()}

    def save_score(self, resume_id: int, opp_id: int, score_data: Dict) -> None:
        db = self.load_json(self.scores_db)
        resume_key = str(resume_id)
        opp_key = str(opp_id)

        if resume_key not in db['scores']:
            db['scores'][resume_key] = {}
        db['scores'][resume_key][opp_key] = {
            **score_data,
            'scored_at': datetime.now().isoformat()
        }
        self.save_json(self.scores_db, db)
        logger.debug(f"Saved score: Resume {resume_id} X Opportunity {opp_id} = {score_data.get('overall', 'N/A')}")

    def get_score(self, resume_id: int, opp_id: int) -> Optional[Dict]:
        db = self.load_json(self.scores_db)
        resume_scores = db['scores'].get(str(resume_id), {})
        return resume_scores.get(str(opp_id))

    def get_resume_scores(self, resume_id: int) -> Dict[int, Dict]:
        db = self.load_json(self.scores_db)
        resume_scores = db['scores'].get(str(resume_id), {})
        return {int(k): v for k, v in resume_scores.items()}

    def get_opportunity_scores(self, opp_id: int) -> Dict[int, Dict]:
        db = self.load_json(self.scores_db)
        opp_scores = {}

        for resume_id, scores in db['scores'].items():
            if str(opp_id) in scores:
                opp_scores[int(resume_id)] = scores[str(opp_id)]

        return opp_scores

    def resume_needs_scoring(self, resume_id: int, opp_id: int) -> bool:
        return self.get_score(resume_id, opp_id) is None

    def get_low_scoring_resumes(self, threshold: int = 70) -> List[Dict]:
        db = self.load_json(self.scores_db)
        resumes_db = self.load_json(self.resumes_db)
        opportunities_db = self.load_json(self.opportunities_db)

        total_opportunities = len(opportunities_db['opportunities'])
        if total_opportunities == 0:
            return []

        low_scorers = []

        for resume_id, scores in db['scores'].items():
            if len(scores) != total_opportunities:
                continue
            all_low = all(
                score_data.get('overall', 0) < threshold
                for score_data in scores.values()
            )

            if all_low:
                resume_data = resumes_db['resumes'].get(resume_id, {})
                low_scorers.append({
                    'resume_id': int(resume_id),
                    'filename': resume_data.get('filename'),
                    'email': resume_data.get('email'),
                    'phone': resume_data.get('phone'),
                    'scores': {int(k): v for k, v in scores.items()}
                })

        return low_scorers

    def update_metadata(self) -> None:
        resumes_db = self.load_json(self.resumes_db)
        opportunities_db = self.load_json(self.opportunities_db)
        scores_db = self.load_json(self.scores_db)

        total_scores = sum(len(scores) for scores in scores_db['scores'].values())

        metadata = {
            'last_check': datetime.now().isoformat(),
            'total_resumes': len(resumes_db['resumes']),
            'total_opportunities': len(opportunities_db['opportunities']),
            'total_scores': total_scores
        }

        self.save_json(self.metadata_db, metadata)

    def get_metadata(self) -> Dict:
        return self.load_json(self.metadata_db)