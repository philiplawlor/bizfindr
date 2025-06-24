""
Tests for the BizFindr API endpoints.
"""

import json
from datetime import datetime, timedelta

import pytest
from bson import ObjectId

# Test data
SAMPLE_BUSINESS = {
    'business_id': 'CT99999999',
    'name': 'Test API Business',
    'type': 'LLC',
    'status': 'Active',
    'registration_date': (datetime.utcnow() - timedelta(days=10)).isoformat(),
    'address': {
        'street': '123 Test St',
        'city': 'Hartford',
        'state': 'CT',
        'zip': '06103',
        'county': 'Hartford'
    },
    'officers': [
        {'name': 'API Test User', 'title': 'CEO'}
    ],
    'registered_agent': 'Test Agent LLC',
    'agent_address': '456 Agent St, Hartford, CT 06103'
}

def test_get_businesses(client, db):
    """Test getting a list of businesses."""
    # Add a test business
    db.businesses.insert_one(SAMPLE_BUSINESS)
    
    # Make request
    response = client.get('/api/businesses')
    data = json.loads(response.data)
    
    # Assertions
    assert response.status_code == 200
    assert 'businesses' in data
    assert len(data['businesses']) > 0
    assert any(b['business_id'] == 'CT99999999' for b in data['businesses'])

def test_get_business(client, db):
    """Test getting a single business by ID."""
    # Add a test business
    result = db.businesses.insert_one(SAMPLE_BUSINESS)
    business_id = str(result.inserted_id)
    
    # Make request
    response = client.get(f'/api/businesses/{business_id}')
    data = json.loads(response.data)
    
    # Assertions
    assert response.status_code == 200
    assert data['name'] == 'Test API Business'
    assert data['business_id'] == 'CT99999999'

def test_get_nonexistent_business(client):
    """Test getting a business that doesn't exist."""
    # Make request with non-existent ID
    response = client.get('/api/businesses/507f1f77bcf86cd799439011')
    
    # Assertions
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'not found' in data['message'].lower()

def test_search_businesses(client, db):
    """Test searching for businesses."""
    # Add test businesses
    db.businesses.insert_many([
        SAMPLE_BUSINESS,
        {
            'business_id': 'CT11111111',
            'name': 'Another Test Business',
            'type': 'Corporation',
            'status': 'Active',
            'registration_date': datetime.utcnow().isoformat(),
            'address': {
                'city': 'New Haven',
                'state': 'CT',
                'zip': '06510'
            },
            'officers': [{'name': 'John Smith', 'title': 'CEO'}]
        }
    ])
    
    # Test search by name
    response = client.get('/api/businesses/search?q=Test+API')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert len(data['results']) == 1
    assert data['results'][0]['name'] == 'Test API Business'
    
    # Test search by city
    response = client.get('/api/businesses/search?city=New+Haven')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert len(data['results']) == 1
    assert data['results'][0]['name'] == 'Another Test Business'

def test_business_statistics(client, db):
    """Test getting business statistics."""
    # Add test businesses
    db.businesses.insert_many([
        {'type': 'LLC', 'status': 'Active', 'registration_date': datetime.utcnow()},
        {'type': 'LLC', 'status': 'Active', 'registration_date': datetime.utcnow()},
        {'type': 'Corporation', 'status': 'Active', 'registration_date': datetime.utcnow()},
        {'type': 'LLP', 'status': 'Inactive', 'registration_date': datetime.utcnow()}
    ])
    
    # Make request
    response = client.get('/api/statistics')
    data = json.loads(response.data)
    
    # Assertions
    assert response.status_code == 200
    assert data['total_businesses'] == 4
    assert data['business_types']['LLC'] == 2
    assert data['business_types']['Corporation'] == 1
    assert data['business_statuses']['Active'] == 3
    assert data['business_statuses']['Inactive'] == 1

@pytest.mark.parametrize('endpoint', [
    '/api/businesses',
    '/api/statistics',
    '/api/refresh'
])
def test_cors_headers(client, endpoint):
    """Test that CORS headers are set correctly."""
    # Make a preflight request
    response = client.options(
        endpoint,
        headers={
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET'
        }
    )
    
    # Assertions
    assert response.status_code == 200
    assert 'Access-Control-Allow-Origin' in response.headers
    assert 'Access-Control-Allow-Methods' in response.headers
    assert 'Access-Control-Allow-Headers' in response.headers

def test_refresh_endpoint_requires_auth(client):
    """Test that the refresh endpoint requires authentication."""
    # Make request without authentication
    response = client.post('/api/refresh')
    
    # Assertions
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'authentication' in data['message'].lower()

# Add more test cases as needed...
