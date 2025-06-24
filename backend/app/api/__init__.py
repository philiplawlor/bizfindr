"""
API Blueprint for BizFindr application.

This module defines the main API blueprint and registers all API routes.
"""
from flask import Blueprint, current_app, request, jsonify
from flask_restx import Api, Resource, fields, reqparse
from functools import wraps
import logging

# Create API Blueprint
bp = Blueprint('api', __name__)

# Initialize Flask-RESTx API
api = Api(
    bp,
    version='1.0',
    title='BizFindr API',
    description='API for accessing business registration data',
    doc='/docs',
    default='Business Registrations',
    default_label='Business registration operations'
)

# Namespace for all API routes
ns = api.namespace('v1', description='API version 1')

# Health check endpoint
@ns.route('/health')
class HealthCheck(Resource):
    """Health check endpoint for monitoring"""
    
    @api.doc('health_check')
    def get(self):
        """Health check endpoint"""
        return {
            "status": "ok",
            "environment": current_app.config.get('ENV', 'development'),
            "version": current_app.config.get('VERSION', '1.0.0')
        }

# API Models
pagination_model = api.model('Pagination', {
    'page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Number of items per page'),
    'total_pages': fields.Integer(description='Total number of pages'),
    'total_items': fields.Integer(description='Total number of items')
})

registration_model = api.model('Registration', {
    'id': fields.String(description='Unique identifier'),
    'registration_id': fields.String(required=True, description='Registration ID'),
    'business_name': fields.String(required=True, description='Name of the business'),
    'business_type': fields.String(description='Type of business entity'),
    'date_registration': fields.DateTime(description='Date of registration'),
    'status': fields.String(description='Registration status'),
    'address': fields.Nested(api.model('Address', {
        'street': fields.String,
        'city': fields.String,
        'state': fields.String,
        'zip': fields.String
    })),
    'created_at': fields.DateTime(description='When the record was created'),
    'updated_at': fields.DateTime(description='When the record was last updated')
})

# Request parsers
pagination_parser = reqparse.RequestParser()
pagination_parser.add_argument('page', type=int, default=1, help='Page number')
pagination_parser.add_argument('per_page', type=int, default=20, help='Items per page')

search_parser = pagination_parser.copy()
search_parser.add_argument('q', type=str, help='Search query')
search_parser.add_argument('business_type', type=str, help='Filter by business type')
search_parser.add_argument('status', type=str, help='Filter by status')
search_parser.add_argument('date_from', type=str, help='Filter by start date (YYYY-MM-DD)')
search_parser.add_argument('date_to', type=str, help='Filter by end date (YYYY-MM-DD)')
search_parser.add_argument('sort', type=str, default='date_registration', help='Field to sort by')
search_parser.add_argument('order', type=str, choices=('asc', 'desc'), default='desc', help='Sort order')

def api_key_required(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != current_app.config['API_KEY']:
            return {'error': 'unauthorized', 'message': 'Missing or invalid API key'}, 401
        return f(*args, **kwargs)
    return decorated_function

@ns.route('/registrations')
class RegistrationList(Resource):
    @ns.doc('list_registrations')
    @ns.expect(pagination_parser)
    @ns.marshal_with(api.model('RegistrationList', {
        'data': fields.List(fields.Nested(registration_model)),
        'pagination': fields.Nested(pagination_model)
    }))
    @api_key_required
    def get(self):
        """List all business registrations with pagination."""
        args = pagination_parser.parse_args()
        page = args['page']
        per_page = args['per_page']
        
        try:
            # Calculate skip value for pagination
            skip = (page - 1) * per_page
            
            # Get total count of registrations
            total = current_app.db.registrations.count_documents({})
            total_pages = (total + per_page - 1) // per_page
            
            # Get paginated registrations
            registrations = list(current_app.db.registrations
                              .find({}, {'_id': 0})
                              .sort('date_registration', -1)
                              .skip(skip)
                              .limit(per_page))
            
            return {
                'data': registrations,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'total_items': total
                }
            }
            
        except Exception as e:
            current_app.logger.error(f'Error fetching registrations: {str(e)}')
            return {'error': 'internal_error', 'message': 'Failed to fetch registrations'}, 500

@ns.route('/registrations/search')
class RegistrationSearch(Resource):
    @ns.doc('search_registrations')
    @ns.expect(search_parser)
    @ns.marshal_with(api.model('SearchResults', {
        'data': fields.List(fields.Nested(registration_model)),
        'meta': fields.Raw(description='Search metadata')
    }))
    @api_key_required
    def get(self):
        """Search business registrations with filters."""
        args = search_parser.parse_args()
        
        try:
            # Build query
            query = {}
            
            # Text search
            if args['q']:
                query['$text'] = {'$search': args['q']}
            
            # Filters
            if args['business_type']:
                query['business_type'] = args['business_type']
            
            if args['status']:
                query['status'] = args['status']
            
            # Date range filter
            date_query = {}
            if args['date_from']:
                date_query['$gte'] = f"{args['date_from']}T00:00:00"
            if args['date_to']:
                date_query['$lte'] = f"{args['date_to']}T23:59:59"
            if date_query:
                query['date_registration'] = date_query
            
            # Pagination
            page = args['page']
            per_page = args['per_page']
            skip = (page - 1) * per_page
            
            # Get total count
            total = current_app.db.registrations.count_documents(query)
            
            # Sort
            sort_order = -1 if args['order'] == 'desc' else 1
            sort_field = args['sort'] or 'date_registration'
            
            # Execute query
            registrations = list(current_app.db.registrations
                              .find(query, {'_id': 0})
                              .sort(sort_field, sort_order)
                              .skip(skip)
                              .limit(per_page))
            
            return {
                'data': registrations,
                'meta': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'query': {k: v for k, v in args.items() if v is not None}
                }
            }
            
        except Exception as e:
            current_app.logger.error(f'Error searching registrations: {str(e)}')
            return {'error': 'internal_error', 'message': 'Search failed'}, 500

@ns.route('/registrations/<string:registration_id>')
@ns.param('registration_id', 'The registration identifier')
@ns.response(404, 'Registration not found')
class Registration(Resource):
    @ns.doc('get_registration')
    @ns.marshal_with(registration_model)
    @api_key_required
    def get(self, registration_id):
        """Get a specific registration by ID."""
        try:
            registration = current_app.db.registrations.find_one(
                {'registration_id': registration_id},
                {'_id': 0}
            )
            
            if registration is None:
                api.abort(404, 'Registration not found')
                
            return registration
            
        except Exception as e:
            current_app.logger.error(f'Error fetching registration {registration_id}: {str(e)}')
            return {'error': 'internal_error', 'message': 'Failed to fetch registration'}, 500

@ns.route('/registrations/latest-date')
class LatestRegistrationDate(Resource):
    @ns.doc('get_latest_registration_date')
    @ns.marshal_with(api.model('LatestDate', {
        'latest_date': fields.DateTime(description='Date of the most recent registration')
    }))
    @api_key_required
    def get(self):
        """Get the date of the most recent registration in the database."""
        try:
            latest = current_app.db.registrations.find_one(
                {},
                {'date_registration': 1, '_id': 0},
                sort=[('date_registration', -1)]
            )
            
            if not latest or 'date_registration' not in latest:
                return {'latest_date': None}
                
            return {'latest_date': latest['date_registration']}
            
        except Exception as e:
            current_app.logger.error(f'Error fetching latest registration date: {str(e)}')
            return {'error': 'internal_error', 'message': 'Failed to fetch latest registration date'}, 500
