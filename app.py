from flask import Flask, request, jsonify, render_template
from models import MongoDBHandler, format_action_message
from datetime import datetime
import json
import pytz
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

db_handler = MongoDBHandler()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/webhook', methods=['GET', 'POST'])
def webhook_receiver():
    if request.method == 'GET':
        return "Webhook endpoint is working!"
    
    try:
        event_type = request.headers.get('X-GitHub-Event', '')
        payload = request.get_json()
        
        if not payload:
            return jsonify({'error': 'No payload received'}), 400
        
        action_data = None
        
        if event_type == 'push':
            action_data = process_push_event(payload)
        elif event_type == 'pull_request':
            if payload.get('action') == 'closed' and payload.get('pull_request', {}).get('merged'):
                action_data = process_merge_event(payload)
            else:
                action_data = process_pull_request_event(payload)
        
        if action_data:
            success = db_handler.insert_action(action_data)
            if success:
                return jsonify({'status': 'success', 'message': 'Webhook processed successfully'}), 200
            else:
                return jsonify({'error': 'Failed to store data'}), 500
        else:
            return jsonify({'message': 'Event not processed'}), 200
            
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def process_push_event(payload):
    try:
        commits = payload.get('commits', [])
        if not commits:
            return None
            
        latest_commit = commits[-1]
        author = latest_commit.get('author', {}).get('name', 'Unknown')
        ref = payload.get('ref', '')
        to_branch = ref.split('/')[-1] if '/' in ref else 'unknown'
        
        added_files = latest_commit.get('added', [])
        modified_files = latest_commit.get('modified', [])
        removed_files = latest_commit.get('removed', [])
        
        file_changes = {
            'added': added_files,
            'modified': modified_files,
            'removed': removed_files,
            'total_changes': len(added_files) + len(modified_files) + len(removed_files)
        }
        
        return {
            'id': latest_commit.get('id', ''),
            'message': latest_commit.get('message', ''),
            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')),
            'author': author,
            'to_branch': to_branch,
            'from_branch': None,
            'request_type': 'push',
            'file_changes': file_changes,
            'commit_url': latest_commit.get('url', ''),
            'files_changed': file_changes['total_changes']
        }
    except Exception as e:
        print(f"Error processing push event: {e}")
        return None

def process_pull_request_event(payload):
    try:
        pr = payload.get('pull_request', {})
        action = payload.get('action', '')
        if action != 'opened':
            return None
            
        author = pr.get('user', {}).get('login', 'Unknown')
        from_branch = pr.get('head', {}).get('ref', 'unknown')
        to_branch = pr.get('base', {}).get('ref', 'unknown')
        
        return {
            'id': str(pr.get('id', '')),
            'message': pr.get('title', ''),
            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')),
            'author': author,
            'to_branch': to_branch,
            'from_branch': from_branch,
            'request_type': 'pull_request'
        }
    except Exception as e:
        print(f"Error processing pull request event: {e}")
        return None

def process_merge_event(payload):
    try:
        pr = payload.get('pull_request', {})
        if not pr.get('merged', False):
            return None
            
        author = pr.get('merged_by', {}).get('login', 'Unknown')
        from_branch = pr.get('head', {}).get('ref', 'unknown')
        to_branch = pr.get('base', {}).get('ref', 'unknown')
        
        return {
            'id': str(pr.get('id', '')),
            'message': pr.get('title', ''),
            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')),
            'author': author,
            'to_branch': to_branch,
            'from_branch': from_branch,
            'request_type': 'merge'
        }
    except Exception as e:
        print(f"Error processing merge event: {e}")
        return None

@app.route('/api/actions', methods=['GET'])
def get_actions():
    try:
        actions = db_handler.get_recent_actions()
        formatted_actions = []

        ist = pytz.timezone('Asia/Kolkata')
        for action in actions:
            timestamp = action['timestamp']
            if isinstance(timestamp, datetime):
                timestamp = timestamp.astimezone(ist).isoformat()
            formatted_actions.append({
                'id': action['_id'],
                'message': format_action_message(action),
                'timestamp': timestamp,
                'type': action['request_type']
            })

        return jsonify(formatted_actions)
    except Exception as e:
        print(f"Error fetching actions: {e}")
        return jsonify({'error': 'Failed to fetch actions'}), 500

@app.route('/test-webhook', methods=['GET', 'POST'])
def test_webhook():
    if request.method == 'GET':
        return "Test webhook endpoint is working!"
    
    try:
        test_data = {
            'id': 'test_123',
            'message': 'Test commit message',
            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')),
            'author': 'Test User',
            'to_branch': 'main',
            'from_branch': None,
            'request_type': 'push'
        }
        
        success = db_handler.insert_action(test_data)
        if success:
            return jsonify({'status': 'success', 'message': 'Test data inserted'}), 200
        else:
            return jsonify({'error': 'Failed to insert test data'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
