"""
Frontend Blueprint for BizFindr application.

This module defines the frontend blueprint that handles all the frontend routes.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from bson.objectid import ObjectId
from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify

from app.services.business_service import BusinessService
from app.db.mongodb import get_database

# Create frontend Blueprint
bp = Blueprint('main', __name__, template_folder='../../../frontend/templates')

# Add current datetime to template context for all routes
@bp.context_processor
def inject_now():
    """Inject current datetime into all templates as 'now'."""
    return {'now': datetime.utcnow()}

@bp.route('/')
def index():
    """Render the index page."""
    # Default stats to prevent template errors
    stats = {
        'total_registrations': 0,
        'latest_registration': None,
        'by_business_type': [],
        'by_status': [],
        'recent_registrations': []
    }
    return render_template('index.html', stats=stats)

@bp.route('/search')
def search():
    """Handle search requests and render search results."""
    # Get query parameters with defaults
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    business_type = request.args.get('business_type', '')
    status = request.args.get('status', '')
    per_page = 10  # Default number of results per page
    
    # In a real implementation, these would come from a database query
    results = []  # This would be a list of search results
    total = 0     # Total number of results
    total_pages = 1  # Total number of pages
    
    # Pass all required variables to the template
    return render_template(
        'search.html',
        query=query,
        page=page,
        per_page=per_page,
        business_type=business_type,
        status=status,
        results=results,
        total=total,
        total_pages=total_pages,
        current_filters={
            'business_type': business_type,
            'status': status
        }
    )

@bp.route('/registration/<registration_id>')
def registration_detail(registration_id):
    """Render the registration detail page."""
    return render_template('registration_detail.html', registration_id=registration_id)

@bp.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

@bp.route('/api/stats')
async def api_stats():
    """API endpoint to get statistics for the dashboard."""
    try:
        db = get_database()
        business_service = BusinessService(db)
        
        # Get total number of businesses
        total_businesses = await db.businesses.count_documents({})
        
        # Get latest registration
        latest_business = await db.businesses.find_one(
            {},
            sort=[('created_at', -1)],
            projection={
                'business_name': 1,
                'business_type': 1,
                'status': 1,
                'created_at': 1
            }
        )
        
        # Get count by business type
        pipeline = [
            {'$group': {
                '_id': '$business_type',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]
        by_business_type = await db.businesses.aggregate(pipeline).to_list(None)
        
        # Get count by status
        pipeline = [
            {'$group': {
                '_id': '$status',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]
        by_status = await db.businesses.aggregate(pipeline).to_list(None)
        
        # Get recent registrations
        recent_registrations = await db.businesses.find(
            {},
            {
                'business_name': 1,
                'business_type': 1,
                'status': 1,
                'created_at': 1,
                'address.city': 1,
                'address.state': 1
            }
        ).sort('created_at', -1).limit(5).to_list(None)
        
        # Format the response
        stats = {
            'total_registrations': total_businesses,
            'latest_registration': {
                'business_name': latest_business.get('business_name', 'N/A') if latest_business else 'N/A',
                'business_type': latest_business.get('business_type', 'N/A') if latest_business else 'N/A',
                'status': latest_business.get('status', 'N/A') if latest_business else 'N/A',
                'created_at': latest_business.get('created_at', '').isoformat() if latest_business else 'N/A'
            } if latest_business else None,
            'by_business_type': by_business_type or [],
            'by_status': by_status or [],
            'recent_registrations': [
                {
                    'business_name': r.get('business_name', 'N/A'),
                    'business_type': r.get('business_type', 'N/A'),
                    'status': r.get('status', 'N/A'),
                    'city': r.get('address', {}).get('city', 'N/A'),
                    'state': r.get('address', {}).get('state', 'N/A'),
                    'created_at': r.get('created_at', '').isoformat() if r.get('created_at') else 'N/A'
                }
                for r in (recent_registrations or [])
            ]
        }
        
        return jsonify(stats)
    except Exception as e:
        current_app.logger.error(f'Error fetching stats: {str(e)}')
        # Return default stats on error
        return jsonify({
            'total_registrations': 0,
            'latest_registration': None,
            'by_business_type': [],
            'by_status': [],
            'recent_registrations': [],
            'error': 'Failed to fetch statistics'
        })

@bp.route('/api/refresh', methods=['POST'])
def api_refresh():
    """API endpoint to manually trigger a data refresh."""
    try:
        # In a real implementation, this would trigger a background task to refresh the data
        # For now, we'll just return a success message
        return jsonify({
            'success': True,
            'message': 'Refresh request received. Data will be updated shortly.'
        }), 202  # 202 Accepted
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
