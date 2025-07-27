import os
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase only once
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

def has_been_posted(link: str) -> bool:
    """Checks if a link has already been posted."""
    doc_ref = db.collection("posted_links").document(link)
    return doc_ref.get().exists

def mark_as_posted(link: str):
    """Marks a link as posted."""
    doc_ref = db.collection("posted_links").document(link)
    doc_ref.set({"timestamp": firestore.SERVER_TIMESTAMP})
