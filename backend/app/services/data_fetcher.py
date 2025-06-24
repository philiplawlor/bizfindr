"""
Data Fetcher Service

This module handles fetching business registration data from the CT.gov API
and storing it in the MongoDB database.
"""
import os
import logging
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlencode
from bson import ObjectId

logger = logging.getLogger(__name__)

def fetch_data_from_api(url, params=None):
    """Fetch data from the CT.gov API.
    
    Args:
        url (str): The API endpoint URL
        params (dict, optional): Query parameters. Defaults to None.
        
    Returns:
        tuple: (data, error) where data is the parsed JSON response or None if an error occurred,
              and error is the error message or None if successful.
    """
    try:
        logger.info(f"Fetching data from {url} with params: {params}")
        
        # Set default timeout and headers
        headers = {
            'User-Agent': 'BizFindr/1.0 (https://github.com/yourusername/bizfindr; your-email@example.com)',
            'Accept': 'application/json'
        }
        
        # Make the request
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=30  # 30 seconds timeout
        )
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        logger.info(f"Successfully fetched {len(data) if isinstance(data, list) else 1} records")
        return data, None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"API request failed: {str(e)}"
        logger.error(error_msg)
        return None, error_msg
    except ValueError as e:
        error_msg = f"Failed to parse JSON response: {str(e)}"
        logger.error(error_msg)
        return None, error_msg

def transform_registration_data(record):
    """Transform raw API data to our database schema.
    
    Args:
        record (dict): Raw registration record from the API
        
    Returns:
        dict: Transformed record
    """
    try:
        # Extract and transform the data
        transformed = {
            'registration_id': record.get('registration_id', ''),
            'business_name': record.get('business_name', '').strip(),
            'business_type': record.get('business_type', '').strip(),
            'status': record.get('status', '').strip().capitalize(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Parse date if available
        date_str = record.get('date_registration')
        if date_str:
            try:
                # Try to parse the date string (format may vary)
                if 'T' in date_str:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                transformed['date_registration'] = dt
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse date '{date_str}': {str(e)}")
        
        # Handle address if available
        address = {}
        if 'address' in record and isinstance(record['address'], dict):
            address_fields = ['street', 'city', 'state', 'zip', 'address_1', 'address_2']
            for field in address_fields:
                if field in record['address'] and record['address'][field]:
                    # Map address_1/address_2 to street
                    if field == 'address_1':
                        address['street'] = record['address'][field].strip()
                    elif field == 'address_2' and record['address'][field]:
                        address['street'] = address.get('street', '') + ' ' + record['address'][field].strip()
                    elif field not in ['address_1', 'address_2']:
                        address[field] = record['address'][field].strip()
        
        if address:
            transformed['address'] = address
        
        # Add any additional fields
        additional_fields = [
            'agent_name', 'agent_address', 'filing_date', 'jurisdiction',
            'principal_office_address', 'registered_agent', 'state_id'
        ]
        
        for field in additional_fields:
            if field in record and record[field]:
                transformed[field] = record[field]
        
        return transformed
        
    except Exception as e:
        logger.error(f"Error transforming registration data: {str(e)}")
        return None

def save_registrations(db, registrations):
    """Save registration records to the database.
    
    Args:
        db: MongoDB database instance
        registrations (list): List of registration records to save
        
    Returns:
        tuple: (saved_count, error_count, errors)
    """
    if not registrations:
        return 0, 0, []
    
    saved_count = 0
    error_count = 0
    errors = []
    
    for record in registrations:
        try:
            # Transform the record
            transformed = transform_registration_data(record)
            if not transformed:
                error_count += 1
                errors.append({
                    'record': record.get('registration_id', str(record)[:100]),
                    'error': 'Failed to transform record'
                })
                continue
            
            # Check if record already exists
            existing = db.registrations.find_one(
                {'registration_id': transformed['registration_id']}
            )
            
            if existing:
                # Update existing record
                update_data = {k: v for k, v in transformed.items() 
                             if k not in ['_id', 'created_at']}
                update_data['updated_at'] = datetime.utcnow()
                
                result = db.registrations.update_one(
                    {'_id': existing['_id']},
                    {'$set': update_data}
                )
                
                if result.modified_count > 0:
                    saved_count += 1
            else:
                # Insert new record
                db.registrations.insert_one(transformed)
                saved_count += 1
                
        except Exception as e:
            error_count += 1
            error_msg = str(e)
            logger.error(f"Error saving record: {error_msg}")
            errors.append({
                'record': record.get('registration_id', str(record)[:100]),
                'error': error_msg
            })
    
    return saved_count, error_count, errors

def fetch_latest_data():
    """Fetch the latest data from the CT.gov API and save to database.
    
    Returns:
        dict: Result of the operation with count of records processed and any errors
    """
    from flask import current_app
    
    try:
        # Get the latest registration date from our database
        latest_record = current_app.db.registrations.find_one(
            {},
            sort=[('date_registration', -1)]
        )
        
        # Set up the API URL and parameters
        base_url = current_app.config['API_BASE_URL']
        params = {
            '$order': 'date_registration ASC',  # Get oldest first
            '$limit': 1000  # Socrata default limit
        }
        
        # Add date filter if we have a latest record
        if latest_record and 'date_registration' in latest_record:
            last_date = latest_record['date_registration']
            if isinstance(last_date, str):
                # If it's a string, ensure it's in the right format
                last_date = datetime.fromisoformat(last_date.replace('Z', '+00:00'))
            
            # Add one second to avoid fetching the same record again
            next_date = last_date + timedelta(seconds=1)
            params['$where'] = f"date_registration >= '{next_date.isoformat()}'"
        
        # Fetch data from the API
        data, error = fetch_data_from_api(base_url, params)
        
        if error:
            return {
                'success': False,
                'error': error,
                'count': 0,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        if not data or not isinstance(data, list):
            return {
                'success': True,
                'message': 'No new data available',
                'count': 0,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Save the data to the database
        saved_count, error_count, errors = save_registrations(current_app.db, data)
        
        # Log the fetch operation
        fetch_log = {
            'timestamp': datetime.utcnow(),
            'records_fetched': len(data),
            'records_saved': saved_count,
            'errors': error_count,
            'last_processed_date': datetime.utcnow().isoformat(),
            'status': 'success' if error_count == 0 else 'partial_success'
        }
        
        if error_count > 0:
            fetch_log['error_details'] = errors[:10]  # Store first 10 errors
            
        current_app.db.fetch_history.insert_one(fetch_log)
        
        return {
            'success': True,
            'count': saved_count,
            'errors': error_count,
            'timestamp': datetime.utcnow().isoformat(),
            'message': f'Successfully processed {saved_count} records with {error_count} errors'
        }
        
    except Exception as e:
        error_msg = f"Failed to fetch latest data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Log the error
        current_app.db.fetch_history.insert_one({
            'timestamp': datetime.utcnow(),
            'status': 'error',
            'error': error_msg
        })
        
        return {
            'success': False,
            'error': error_msg,
            'count': 0,
            'timestamp': datetime.utcnow().isoformat()
        }
