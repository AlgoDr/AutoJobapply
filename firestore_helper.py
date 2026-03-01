import os, logging
from typing import Optional, Dict
try:
    from google.cloud import firestore
    FIRESTORE_AVAILABLE = True
except Exception:
    firestore = None
    FIRESTORE_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory fallback for local/dev when ADC not configured
_INMEM_USERS = {}
_INMEM_APPLICATIONS = []  # list of dict(user_id, job_id, timestamp)

def _get_client():
    if FIRESTORE_AVAILABLE:
        try:
            project = os.getenv('PROJECT_ID')
            if project:
                return firestore.Client(project=project)
            return firestore.Client()
        except Exception as e:
            logger.warning('Firestore client init failed: %s', e)
            return None
    return None

def save_user_profile(user_id: str, profile: Dict) -> bool:
    """Saves/updates a user profile keyed by user_id. Falls back to in-memory if Firestore not available."""
    client = _get_client()
    if client:
        try:
            doc_ref = client.collection('users').document(user_id)
            doc_ref.set(profile)
            return True
        except Exception as e:
            logger.exception('Failed to save profile to Firestore: %s', e)
            return False
    # fallback: save by user_id and also by name for lookup
    _INMEM_USERS[user_id] = profile
    if profile.get('name'):
        _INMEM_USERS.setdefault('__by_name__', {})[profile['name'].lower()] = profile
    return True

def find_user_by_name(name: str):
    client = _get_client()
    if client:
        try:
            docs = client.collection('users').where('name', '==', name).limit(1).stream()
            for d in docs:
                data = d.to_dict()
                data['_id'] = d.id
                return data
            return None
        except Exception as e:
            logger.exception('Firestore name lookup failed: %s', e)
            return None
    return _INMEM_USERS.get('__by_name__', {}).get(name.lower())

def get_user_by_id(user_id: str):
    client = _get_client()
    if client:
        try:
            doc = client.collection('users').document(user_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['_id'] = doc.id
                return data
            return None
        except Exception as e:
            logger.exception('Failed to get user by id: %s', e)
            return None
    return _INMEM_USERS.get(user_id)

def log_application(user_id: str, job_id: str, timestamp=None) -> bool:
    client = _get_client()
    record = {'user_id': user_id, 'job_id': job_id, 'timestamp': timestamp}
    if client:
        try:
            client.collection('applications').add(record)
            return True
        except Exception as e:
            logger.exception('Failed to log application to Firestore: %s', e)
            return False
    _INMEM_APPLICATIONS.append(record)
    return True

def get_applications_for_today(user_id: str):
    # simple in-memory filter for demo
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    client = _get_client()
    if client:
        try:
            docs = client.collection('applications').where('user_id', '==', user_id).stream()
            return [d.to_dict() for d in docs]
        except Exception as e:
            logger.exception('Failed to query applications: %s', e)
            return []
    return [r for r in _INMEM_APPLICATIONS if r.get('user_id') == user_id]