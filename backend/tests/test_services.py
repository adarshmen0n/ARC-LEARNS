import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from app.services.text_cleaner import clean_text
from app.services.chunker import create_chunks
from app.services.vector_store import create_vector_store, search
from app.services.chapter_detector import detect_chapters
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_home_endpoint():
    response = client.get('/')
    assert response.status_code == 200
    data = response.json()
    assert 'ARC LEARNS' in data['message']

def test_text_cleaner():
    raw = 'Hello   world!\n\nParagraph two with <b>bold</b>.\n\n`python\nx = 1\n`'
    cleaned = clean_text(raw)
    assert '\n\n' in cleaned
    assert 'x = 1' in cleaned

def test_chunker():
    sample = 'ARC LEARNS AI system test. ' * 50
    chunks = create_chunks(sample, chunk_size=100, overlap=20)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) > 0

def test_chapter_detector():
    doc = '# Chapter 1: Introduction\nSome content here.\n\n## Chapter 2: Foundations\nMore content.'
    chapters = detect_chapters(doc)
    assert len(chapters) >= 2

def test_vector_store():
    docs = [
        'Kahn algorithm DAG topological sorting for curriculum sequencing.',
        'Adaptive learning rate and exponential moving average.',
        'Game mechanics integrated with cognitive mastery levels.'
    ]
    create_vector_store(docs)
    results = search('topological sorting', top_k=1)
    assert len(results) > 0
    assert 'Kahn' in results[0]
