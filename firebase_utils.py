import os
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
# Initialize Firebase only once
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

def _link_id(link: str) -> str:
    return hashlib.sha256(link.encode()).hexdigest()

def has_been_posted(link: str) -> bool:
    doc_ref = db.collection("posted_links").document(_link_id(link))
    return doc_ref.get().exists

def mark_as_posted(link: str):
    doc_ref = db.collection("posted_links").document(_link_id(link))
    doc_ref.set({
        "link": link,
        "timestamp": firestore.SERVER_TIMESTAMP
    })