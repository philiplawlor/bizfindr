"""
Pytest configuration and fixtures for testing the BizFindr application.
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from flask import Flask
from pymongo import MongoClient
from pymongo.database import Database

# Add the project root to the Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app import create_app
from backend.app.extensions import mongo

# Test database configuration
TEST_DB_NAME = 'bizfindr_test'
TEST_MONGO_URI = f'mongodb://localhost:27017/{TEST_DB_NAME}'

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for testing."""
    # Create a test config
    config = {
        'TESTING': True,
        'DEBUG': True,
        'MONGO_URI': TEST_MONGO_URI,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
    }
    
    # Create the app with test config
    app = create_app(config)
    
    # Establish an application context before running the tests
    ctx = app.app_context()
    ctx.push()
    
    yield app
    
    # Clean up after tests
    ctx.pop()

@pytest.fixture(scope='function')
def client(app):
    """A test client for the app."""
    with app.test_client() as client:
        yield client

@pytest.fixture(scope='function')
def db(app):
    """Get a test database instance."""
    # Drop the test database before each test
    with app.app_context():
        # Get the test database
        test_db = mongo.db.client[TEST_DB_NAME]
        
        # Clean up any existing data
        for collection in test_db.list_collection_names():
            test_db[collection].drop()
        
        # Set up any initial test data
        setup_test_data(test_db)
        
        yield test_db
        
        # Clean up after test
        for collection in test_db.list_collection_names():
            test_db[collection].drop()

def setup_test_data(db):
    """Set up initial test data in the database."""
    # Sample business data
    businesses = [
        {
            'business_id': 'CT12345678',
            'name': 'Test Business 1',
            'type': 'LLC',
            'status': 'Active',
            'registration_date': datetime.utcnow() - timedelta(days=30),
            'address': {
                'street': '123 Test St',
                'city': 'Hartford',
                'state': 'CT',
                'zip': '06103',
                'county': 'Hartford'
            },
            'officers': [
                {'name': 'John Doe', 'title': 'CEO'},
                {'name': 'Jane Smith', 'title': 'CFO'}
            ],
            'registered_agent': 'Test Agent LLC',
            'agent_address': '456 Agent St, Hartford, CT 06103',
            'last_updated': datetime.utcnow()
        },
        {
            'business_id': 'CT87654321',
            'name': 'Test Business 2',
            'type': 'Corporation',
            'status': 'Active',
            'registration_date': datetime.utcnow() - timedelta(days=15),
            'address': {
                'street': '789 Example Ave',
                'city': 'New Haven',
                'state': 'CT',
                'zip': '06510',
                'county': 'New Haven'
            },
            'officers': [
                {'name': 'Alice Johnson', 'title': 'President'}
            ],
            'registered_agent': 'Legal Services Inc',
            'agent_address': '321 Service Rd, New Haven, CT 06510',
            'last_updated': datetime.utcnow()
        }
    ]
    
    # Insert test data
    if 'businesses' not in db.list_collection_names():
        db.create_collection('businesses')
    
    db.businesses.insert_many(businesses)

@pytest.fixture
def mock_requests():
    """Fixture for mocking requests."""
    with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
        yield {'get': mock_get, 'post': mock_post}

@pytest.fixture
def mock_datetime_now():
    """Fixture for mocking datetime.now()."""
    test_now = datetime(2023, 1, 1, 12, 0, 0)
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = test_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield test_now

@pytest.fixture
authed_client(app, client):
    """A test client with an authenticated user."""
    with client.session_transaction() as session:
        # Simulate a logged-in user
        session['user_id'] = 'testuser123'
        session['email'] = 'test@example.com'
        session['name'] = 'Test User'
    
    yield client
    
    # Clean up the session after the test
    with client.session_transaction() as session:
        session.clear()
