""
Tests for the BizFindr service layer.
"""

from datetime import datetime, timedelta
import pytest
from unittest.mock import patch, MagicMock

from backend.app.services.data_service import DataService
from backend.app.core.errors import NotFoundError, ValidationError

def test_get_businesses(db):
    """Test retrieving a list of businesses."""
    # Setup test data
    test_businesses = [
        {
            'business_id': 'CT12345678',
            'name': 'Test Business 1',
            'type': 'LLC',
            'status': 'Active'
        },
        {
            'business_id': 'CT87654321',
            'name': 'Test Business 2',
            'type': 'Corporation',
            'status': 'Active'
        }
    ]
    db.businesses.insert_many(test_businesses)
    
    # Test with no filters
    result = DataService.get_businesses()
    assert len(result) == 2
    assert result[0]['name'] in ['Test Business 1', 'Test Business 2']
    
    # Test with type filter
    result = DataService.get_businesses(business_type='LLC')
    assert len(result) == 1
    assert result[0]['type'] == 'LLC'

def test_get_business(db):
    """Test retrieving a single business by ID."""
    # Setup test data
    business = {
        'business_id': 'CT12345678',
        'name': 'Test Business',
        'type': 'LLC',
        'status': 'Active'
    }
    result = db.businesses.insert_one(business)
    business_id = str(result.inserted_id)
    
    # Test existing business
    result = DataService.get_business(business_id)
    assert result['name'] == 'Test Business'
    
    # Test non-existent business
    with pytest.raises(NotFoundError):
        DataService.get_business('507f1f77bcf86cd799439011')

def test_search_businesses(db):
    """Test searching for businesses."""
    # Setup test data
    test_businesses = [
        {
            'business_id': 'CT11111111',
            'name': 'Acme Corporation',
            'type': 'Corporation',
            'status': 'Active',
            'address': {
                'city': 'Hartford',
                'state': 'CT'
            },
            'officers': [{'name': 'John Smith', 'title': 'CEO'}]
        },
        {
            'business_id': 'CT22222222',
            'name': 'Acme LLC',
            'type': 'LLC',
            'status': 'Active',
            'address': {
                'city': 'New Haven',
                'state': 'CT'
            },
            'officers': [{'name': 'Jane Doe', 'title': 'CEO'}]
        },
        {
            'business_id': 'CT33333333',
            'name': 'Test Business',
            'type': 'LLC',
            'status': 'Inactive',
            'address': {
                'city': 'Hartford',
                'state': 'CT'
            }
        }
    ]
    db.businesses.insert_many(test_businesses)
    
    # Test search by name
    results = DataService.search_businesses(query='Acme')
    assert len(results) == 2
    assert all('Acme' in b['name'] for b in results)
    
    # Test filter by city
    results = DataService.search_businesses(city='New Haven')
    assert len(results) == 1
    assert results[0]['name'] == 'Acme LLC'
    
    # Test filter by status
    results = DataService.search_businesses(status='Active')
    assert len(results) == 2
    assert all(b['status'] == 'Active' for b in results)
    
    # Test pagination
    results = DataService.search_businesses(limit=1, offset=1)
    assert len(results) == 1

def test_get_business_statistics(db):
    """Test generating business statistics."""
    # Setup test data
    test_businesses = [
        {'type': 'LLC', 'status': 'Active'},
        {'type': 'LLC', 'status': 'Active'},
        {'type': 'Corporation', 'status': 'Active'},
        {'type': 'LLP', 'status': 'Inactive'},
        {'type': 'Nonprofit', 'status': 'Active'}
    ]
    db.businesses.insert_many(test_businesses)
    
    stats = DataService.get_business_statistics()
    
    assert stats['total_businesses'] == 5
    assert stats['business_types']['LLC'] == 2
    assert stats['business_types']['Corporation'] == 1
    assert stats['business_statuses']['Active'] == 4
    assert stats['business_statuses']['Inactive'] == 1

@patch('backend.app.services.data_service.requests')
def test_fetch_business_data(mock_requests, db):
    """Test fetching business data from the CT.gov API."""
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'results': [
            {
                'BusinessID': 'CT12345678',
                'BusinessName': 'Test Business',
                'BusinessType': 'LLC',
                'BusinessStatus': 'Active',
                'BusinessCreationDate': '2023-01-01',
                'PrincipalOfficeAddress': {
                    'AddressLine1': '123 Test St',
                    'City': 'Hartford',
                    'State': 'CT',
                    'PostalCode': '06103'
                },
                'RegisteredAgent': {
                    'Name': 'Test Agent',
                    'Address': '456 Agent St, Hartford, CT 06103'
                },
                'Officers': [
                    {'Name': 'John Doe', 'Title': 'CEO'}
                ]
            }
        ]
    }
    mock_requests.get.return_value = mock_response
    
    # Test the fetch function
    result = DataService.fetch_business_data()
    
    # Assertions
    assert result['added'] == 1
    assert result['updated'] == 0
    assert result['total'] == 1
    
    # Verify the data was saved to the database
    business = db.businesses.find_one({'business_id': 'CT12345678'})
    assert business is not None
    assert business['name'] == 'Test Business'
    assert business['type'] == 'LLC'
    assert business['status'] == 'Active'

@patch('backend.app.services.data_service.requests')
def test_fetch_business_data_error(mock_requests):
    """Test error handling when fetching business data fails."""
    # Mock a failed API response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = 'Internal Server Error'
    mock_requests.get.return_value = mock_response
    
    # Test that an exception is raised
    with pytest.raises(Exception) as exc_info:
        DataService.fetch_business_data()
    
    assert 'Failed to fetch data' in str(exc_info.value)

def test_update_business(db):
    """Test updating a business record."""
    # Setup test data
    business = {
        'business_id': 'CT12345678',
        'name': 'Old Business Name',
        'type': 'LLC',
        'status': 'Active'
    }
    result = db.businesses.insert_one(business)
    business_id = str(result.inserted_id)
    
    # Update the business
    update_data = {'name': 'New Business Name', 'status': 'Inactive'}
    updated = DataService.update_business(business_id, update_data)
    
    # Assertions
    assert updated is True
    
    # Verify the update in the database
    updated_business = db.businesses.find_one({'_id': result.inserted_id})
    assert updated_business['name'] == 'New Business Name'
    assert updated_business['status'] == 'Inactive'

def test_delete_business(db):
    """Test deleting a business record."""
    # Setup test data
    business = {
        'business_id': 'CT12345678',
        'name': 'Business to Delete',
        'type': 'LLC',
        'status': 'Active'
    }
    result = db.businesses.insert_one(business)
    business_id = str(result.inserted_id)
    
    # Delete the business
    deleted = DataService.delete_business(business_id)
    
    # Assertions
    assert deleted is True
    
    # Verify the business was deleted
    assert db.businesses.find_one({'_id': result.inserted_id}) is None
