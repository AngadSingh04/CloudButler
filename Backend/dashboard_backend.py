# Local Backend code for Dashboard Analytics

from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import boto3
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json
from collections import defaultdict, Counter
import os
from boto3.dynamodb.conditions import Key, Attr

app = Flask(__name__)
CORS(app)  # enable CORS for frontend access

# initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1') 
user_profiles_table = dynamodb.Table('VirtualAssistant-UserProfiles')
conversation_history_table = dynamodb.Table('VirtualAssistant-ConversationHistory')
usage_analytics_table = dynamodb.Table('VirtualAssistant-UsageAnalytics')

# initialize S3
s3_client = boto3.client('s3', region_name='us-east-1')

class DashboardAnalytics:
    @staticmethod
    def decimal_to_native(obj):
        """Convert Decimal objects to native Python types for JSON serialization"""
        if isinstance(obj, list):
            return [DashboardAnalytics.decimal_to_native(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: DashboardAnalytics.decimal_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        else:
            return obj

    @staticmethod
    def get_total_requests():
        """Get total requests from analytics table"""
        try:
            response = usage_analytics_table.scan(
                FilterExpression=Attr('metric_type').eq('total_requests')
            )
            total = sum(item.get('count', 0) for item in response['Items'])
            return int(total)
        except Exception as e:
            print(f"Error getting total requests: {e}")
            return 0

    @staticmethod
    def get_active_users_count():
        """Get count of users who interacted in the last 24 hours"""
        try:
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            
            
            response = conversation_history_table.scan(
                FilterExpression=Attr('timestamp').gte(yesterday)
            )
            
            unique_users = set()
            for item in response['Items']:
                unique_users.add(item['user_id'])
            
            return len(unique_users)
        except Exception as e:
            print(f"Error getting active users: {e}")
            return 0

    @staticmethod
    def get_total_friends():
        """Get total number of friends from a specific user"""
        try:
            
            response = user_profiles_table.scan()
            
            if not response['Items']:
                return 0
            
            
            sorted_users = sorted(response['Items'], key=lambda x: x['user_id'])
            
            
            if len(sorted_users) >= 2:
                target_user = sorted_users[1] 
            else:
                target_user = sorted_users[-1]  
            
            friends = target_user.get('friends', [])
            return len(friends) if friends else 0
            
        except Exception as e:
            print(f"Error getting total friends: {e}")
            return 0

    @staticmethod
    def get_s3_bucket_count():
        """Get total number of S3 buckets"""
        try:
            response = s3_client.list_buckets()
            bucket_count = len(response.get('Buckets', []))
            return bucket_count
        except Exception as e:
            print(f"Error getting S3 bucket count: {e}")
            return 0

    @staticmethod
    def get_s3_bucket_details():
        """Get detailed information about S3 buckets"""
        try:
            response = s3_client.list_buckets()
            buckets = response.get('Buckets', [])
            
            bucket_details = []
            total_objects = 0
            total_size = 0
            
            for bucket in buckets:
                bucket_name = bucket['Name']
                created_date = bucket['CreationDate'].isoformat() if bucket.get('CreationDate') else 'Unknown'
                
                try:
                    objects_response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1000)
                    object_count = objects_response.get('KeyCount', 0)
                    total_objects += object_count
                    bucket_size = 0  
                    total_size += bucket_size
                    
                except Exception as bucket_error:
                    print(f"Error getting details for bucket {bucket_name}: {bucket_error}")
                    object_count = 0
                    bucket_size = 0
                
                bucket_details.append({
                    'name': bucket_name,
                    'created_date': created_date,
                    'object_count': object_count,
                    'size': bucket_size
                })
            
            return {
                'buckets': bucket_details,
                'total_buckets': len(buckets),
                'total_objects': total_objects,
                'total_size': total_size
            }
        except Exception as e:
            print(f"Error getting S3 bucket details: {e}")
            return {
                'buckets': [],
                'total_buckets': 0,
                'total_objects': 0,
                'total_size': 0
            }

    @staticmethod
    def get_average_response_time():
        """Simulate average response time (you can implement actual timing logic)"""
        return 245  

    @staticmethod
    def get_recent_activity(limit=10):
        """Get recent conversations"""
        try:
            
            response = conversation_history_table.scan()
            
            items = response['Items']
            
            items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            activities = []
            for item in items[:limit]:
                activities.append({
                    'intent': item.get('intent_name', 'Unknown'),
                    'user': item.get('user_id', 'Unknown')[-3:],  
                    'timestamp': item.get('timestamp', ''),
                    'details': item.get('utterance', 'No details'),
                    'request_type': item.get('request_type', 'Unknown')
                })
            
            return activities
        except Exception as e:
            print(f"Error getting recent activity: {e}")
            return []

    @staticmethod
    def get_requests_over_time():
        """Get request counts over time (last 24 hours, grouped by hour)"""
        try:
            
            yesterday = datetime.now() - timedelta(days=1)
            response = conversation_history_table.scan(
                FilterExpression=Attr('timestamp').gte(yesterday.isoformat())
            )
            
           
            hourly_counts = defaultdict(int)
            for item in response['Items']:
                timestamp_str = item.get('timestamp', '')
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        hour_key = timestamp.strftime('%H:00')
                        hourly_counts[hour_key] += 1
                    except:
                        continue
            
            
            timeline = []
            for hour in range(24):
                hour_str = f"{hour:02d}:00"
                timeline.append({
                    'time': hour_str,
                    'requests': hourly_counts.get(hour_str, 0)
                })
            
            return timeline
        except Exception as e:
            print(f"Error getting requests over time: {e}")
            return []

    @staticmethod
    def get_intent_distribution():
        """Get distribution of different intents"""
        try:
            response = conversation_history_table.scan()
            
            intent_counts = Counter()
            for item in response['Items']:
                intent_name = item.get('intent_name', 'Unknown')
                intent_counts[intent_name] += 1
            
            return dict(intent_counts)
        except Exception as e:
            print(f"Error getting intent distribution: {e}")
            return {}

    @staticmethod
    def get_top_users(limit=5):
        """Get top users by interaction count"""
        try:
            
            response = conversation_history_table.scan()
            
            user_stats = defaultdict(lambda: {'interactions': 0, 'friends': 0, 'name': 'Unknown'})
            
            
            for item in response['Items']:
                user_id = item.get('user_id', 'Unknown')
                user_stats[user_id]['interactions'] += 1
            
            
            profiles_response = user_profiles_table.scan()
            for profile in profiles_response['Items']:
                user_id = profile['user_id']
                if user_id in user_stats:
                    user_stats[user_id]['friends'] = len(profile.get('friends', []))
                    user_stats[user_id]['name'] = profile.get('name', f'User-{user_id[-3:]}')
            
            
            sorted_users = sorted(
                user_stats.items(), 
                key=lambda x: x[1]['interactions'], 
                reverse=True
            )
            
            top_users = []
            for user_id, stats in sorted_users[:limit]:
                top_users.append({
                    'name': stats['name'],
                    'interactions': stats['interactions'],
                    'friends': stats['friends']
                })
            
            return top_users
        except Exception as e:
            print(f"Error getting top users: {e}")
            return []

    @staticmethod
    def get_system_health():
        """Get system health metrics"""
        try:
            
            response = usage_analytics_table.scan(
                FilterExpression=Attr('metric_type').begins_with('error_')
            )
            
            total_errors = sum(item.get('count', 0) for item in response['Items'])
            total_requests = DashboardAnalytics.get_total_requests()
            
            success_rate = 100
            if total_requests > 0:
                success_rate = max(0, 100 - (total_errors / total_requests * 100))
            
            return {
                'cpu_usage': 35,  
                'memory_usage': 60,  
                'api_success_rate': round(success_rate, 1)
            }
        except Exception as e:
            print(f"Error getting system health: {e}")
            return {'cpu_usage': 0, 'memory_usage': 0, 'api_success_rate': 100}

# API endpoints
@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """Get main dashboard statistics"""
    try:
        stats = {
            'totalRequests': DashboardAnalytics.get_total_requests(),
            'activeUsers': DashboardAnalytics.get_active_users_count(),
            'totalFriends': DashboardAnalytics.get_total_friends(),
            's3BucketCount': DashboardAnalytics.get_s3_bucket_count(),
            'avgResponseTime': DashboardAnalytics.get_average_response_time(),
            'lastUpdated': datetime.now().isoformat()
        }
        return jsonify(DashboardAnalytics.decimal_to_native(stats))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/activity')
def get_recent_activity():
    """Get recent activity feed"""
    try:
        activities = DashboardAnalytics.get_recent_activity(15)
        return jsonify(DashboardAnalytics.decimal_to_native(activities))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/charts')
def get_chart_data():
    """Get data for charts"""
    try:
        chart_data = {
            'requestsOverTime': DashboardAnalytics.get_requests_over_time(),
            'intentDistribution': DashboardAnalytics.get_intent_distribution()
        }
        return jsonify(DashboardAnalytics.decimal_to_native(chart_data))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/users')
def get_user_insights():
    """Get user insights"""
    try:
        insights = {
            'topUsers': DashboardAnalytics.get_top_users(5),
            'systemHealth': DashboardAnalytics.get_system_health()
        }
        return jsonify(DashboardAnalytics.decimal_to_native(insights))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/s3')
def get_s3_insights():
    """Get S3 bucket insights"""
    try:
        s3_data = DashboardAnalytics.get_s3_bucket_details()
        return jsonify(DashboardAnalytics.decimal_to_native(s3_data))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/all')
def get_all_dashboard_data():
    """Get all dashboard data in one call"""
    try:
        data = {
            'stats': {
                'totalRequests': DashboardAnalytics.get_total_requests(),
                'activeUsers': DashboardAnalytics.get_active_users_count(),
                'totalFriends': DashboardAnalytics.get_total_friends(),
                's3BucketCount': DashboardAnalytics.get_s3_bucket_count(),
                'avgResponseTime': DashboardAnalytics.get_average_response_time()
            },
            'recentActivity': DashboardAnalytics.get_recent_activity(10),
            'chartData': {
                'requestsOverTime': DashboardAnalytics.get_requests_over_time(),
                'intentDistribution': DashboardAnalytics.get_intent_distribution()
            },
            'userInsights': {
                'topUsers': DashboardAnalytics.get_top_users(5),
                'systemHealth': DashboardAnalytics.get_system_health()
            },
            's3Insights': DashboardAnalytics.get_s3_bucket_details(),
            'lastUpdated': datetime.now().isoformat()
        }
        return jsonify(DashboardAnalytics.decimal_to_native(data))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/')
def index():
    """Serve a simple API info page"""
    return jsonify({
        'message': 'Virtual Assistant Dashboard API',
        'version': '1.0.0',
        'endpoints': {
            '/api/dashboard/stats': 'Main statistics (including S3 bucket count)',
            '/api/dashboard/activity': 'Recent activity',
            '/api/dashboard/charts': 'Chart data',
            '/api/dashboard/users': 'User insights',
            '/api/dashboard/s3': 'S3 bucket insights',
            '/api/dashboard/all': 'All dashboard data',
            '/health': 'Health check'
        }
    })

if __name__ == '__main__':
    # make sure your AWS credentials are configured
    print("Starting Dashboard API Server...")
    print("Make sure your AWS credentials are configured!")
    print("Available endpoints:")
    print("  - GET /api/dashboard/all - Get all dashboard data")
    print("  - GET /api/dashboard/stats - Get main stats (including S3)")
    print("  - GET /api/dashboard/s3 - Get S3 bucket insights")
    print("  - GET /api/dashboard/activity - Get recent activity")
    print("  - GET /health - Health check")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
