"""
Main Blueprint

This module contains the main routes and views for the BizFindr application.
"""
from flask import Blueprint, render_template, current_app, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import requests

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Render the home page."""
    # Get some basic stats for the dashboard
    stats = {}
    try:
        # Get total number of registrations
        stats['total_registrations'] = current_app.db.registrations.count_documents({})
        
        # Get the latest registration date
        latest = current_app.db.registrations.find_one(
            {},
            {'date_registration': 1},
            sort=[('date_registration', -1)]
        )
        stats['latest_registration'] = latest.get('date_registration') if latest else None
        
        # Get count by business type
        pipeline = [
            {'$group': {
                '_id': '$business_type',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]
        stats['by_business_type'] = list(current_app.db.registrations.aggregate(pipeline))
        
    except Exception as e:
        current_app.logger.error(f"Error fetching dashboard stats: {str(e)}")
        flash('Error loading dashboard data', 'danger')
    
    return render_template('index.html', stats=stats)

@bp.route('/search')
def search():
    """Render the search page."""
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    results = []
    total = 0
    
    try:
        # Build the search query
        search_query = {}
        
        # Text search
        if query:
            search_query['$text'] = {'$search': query}
        
        # Add filters
        business_type = request.args.get('business_type')
        if business_type:
            search_query['business_type'] = business_type
            
        status = request.args.get('status')
        if status:
            search_query['status'] = status
            
        # Get total count
        total = current_app.db.registrations.count_documents(search_query)
        
        # Calculate pagination
        skip = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page
        
        # Execute query
        results = list(current_app.db.registrations
            .find(search_query, {'_id': 0})
            .sort('date_registration', -1)
            .skip(skip)
            .limit(per_page))
        
    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}")
        flash('An error occurred during search', 'danger')
    
    # Get unique business types for filter dropdown
    business_types = current_app.db.registrations.distinct('business_type')
    
    return render_template(
        'search.html',
        query=query,
        results=results,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        business_types=sorted(business_types),
        current_filters={
            'business_type': request.args.get('business_type', ''),
            'status': request.args.get('status', '')
        }
    )

@bp.route('/registration/<registration_id>')
def registration_detail(registration_id):
    """Render the registration detail page."""
    try:
        # Get the registration
        registration = current_app.db.registrations.find_one(
            {'registration_id': registration_id},
            {'_id': 0}
        )
        
        if not registration:
            flash('Registration not found', 'danger')
            return redirect(url_for('main.search'))
            
        # Get similar registrations (same business type)
        similar = []
        if 'business_type' in registration and registration['business_type']:
            similar = list(current_app.db.registrations.find(
                {
                    'business_type': registration['business_type'],
                    'registration_id': {'$ne': registration_id}
                },
                {'_id': 0, 'registration_id': 1, 'business_name': 1, 'date_registration': 1}
            ).sort('date_registration', -1).limit(5))
        
        return render_template(
            'registration_detail.html',
            registration=registration,
            similar=similar
        )
        
    except Exception as e:
        current_app.logger.error(f"Error fetching registration {registration_id}: {str(e)}")
        flash('An error occurred while fetching the registration', 'danger')
        return redirect(url_for('main.search'))

@bp.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

@bp.route('/api/stats')
def api_stats():
    """Get application statistics."""
    try:
        stats = {
            'total_registrations': current_app.db.registrations.count_documents({}),
            'last_updated': None
        }
        
        # Get the latest fetch time
        latest_fetch = current_app.db.fetch_history.find_one(
            {'status': 'success'},
            sort=[('timestamp', -1)]
        )
        
        if latest_fetch and 'timestamp' in latest_fetch:
            stats['last_updated'] = latest_fetch['timestamp'].isoformat()
        
        return jsonify(stats)
        
    except Exception as e:
        current_app.logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({'error': 'Failed to fetch stats'}), 500

@bp.route('/api/refresh', methods=['POST'])
@login_required
def api_refresh():
    """Trigger a manual data refresh."""
    try:
        from app.services.scheduler import run_immediate_fetch
        result = run_immediate_fetch()
        
        if result.get('success'):
            flash(f"Successfully refreshed {result.get('count', 0)} records", 'success')
        else:
            flash(f"Failed to refresh data: {result.get('error', 'Unknown error')}", 'danger')
            
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error during manual refresh: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Context processor to make variables available to all templates
@bp.app_context_processor
def inject_now():
    """Inject current datetime into all templates."""
    return {'now': datetime.utcnow()}
