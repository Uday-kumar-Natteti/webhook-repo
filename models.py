from pymongo import MongoClient
from datetime import datetime
import os
from typing import Dict, List, Optional

class MongoDBHandler:
    def __init__(self):
        # MongoDB connection string - replace with your actual connection string
        self.connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.client = MongoClient(self.connection_string)
        self.db = self.client['github_webhooks']
        self.collection = self.db['actions']
    
    def insert_action(self, action_data: Dict) -> bool:
        """Insert a new action into MongoDB"""
        try:
            self.collection.insert_one(action_data)
            return True
        except Exception as e:
            print(f"Error inserting action: {e}")
            return False
    
    def get_recent_actions(self, limit: int = 50) -> List[Dict]:
        """Get recent actions sorted by timestamp"""
        try:
            actions = list(self.collection.find({}).sort("timestamp", -1).limit(limit))
            # Convert ObjectId to string for JSON serialization
            for action in actions:
                action['_id'] = str(action['_id'])
            return actions
        except Exception as e:
            print(f"Error fetching actions: {e}")
            return []
    
    def close_connection(self):
        """Close MongoDB connection"""
        self.client.close()

def format_action_message(action: Dict) -> str:
    """Format action data into display message with file details"""
    action_type = action.get('request_type', '').upper()
    author = action.get('author', 'Unknown')
    timestamp = action.get('timestamp', datetime.now())
    
    # Format timestamp
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            timestamp = datetime.now()
    
    formatted_time = timestamp.strftime("%d %B %Y - %I:%M %p UTC")
    
    if action_type == 'PUSH':
        to_branch = action.get('to_branch', 'unknown')
        base_message = f'"{author}" pushed to "{to_branch}"'
        
        # Add file changes if available
        file_changes = action.get('file_changes', {})
        if file_changes and file_changes.get('total_changes', 0) > 0:
            changes_parts = []
            
            # Added files
            if file_changes.get('added'):
                added_files = file_changes['added']
                if len(added_files) <= 3:
                    changes_parts.append(f"Added: {', '.join(added_files)}")
                else:
                    changes_parts.append(f"Added: {', '.join(added_files[:3])} (+{len(added_files) - 3} more)")
            
            # Modified files  
            if file_changes.get('modified'):
                modified_files = file_changes['modified']
                if len(modified_files) <= 3:
                    changes_parts.append(f"✏Modified: {', '.join(modified_files)}")
                else:
                    changes_parts.append(f"✏Modified: {', '.join(modified_files[:3])} (+{len(modified_files) - 3} more)")
            
            # Removed files
            if file_changes.get('removed'):
                removed_files = file_changes['removed']
                if len(removed_files) <= 3:
                    changes_parts.append(f"🗑Removed: {', '.join(removed_files)}")
                else:
                    changes_parts.append(f"🗑Removed: {', '.join(removed_files[:3])} (+{len(removed_files) - 3} more)")
            
            if changes_parts:
                base_message += f"\n{' | '.join(changes_parts)}"
        
        return f"{base_message}\n{formatted_time}"
    
    elif action_type == 'PULL_REQUEST':
        from_branch = action.get('from_branch', 'unknown')
        to_branch = action.get('to_branch', 'unknown')
        base_message = f'"{author}" submitted a pull request from "{from_branch}" to "{to_branch}"'
        
        # Add commit message if available
        commit_message = action.get('message', '')
        if commit_message:
            base_message += f"\n {commit_message}"
        
        return f"{base_message}\n{formatted_time}"
    
    elif action_type == 'MERGE':
        from_branch = action.get('from_branch', 'unknown')
        to_branch = action.get('to_branch', 'unknown')
        base_message = f'"{author}" merged branch "{from_branch}" to "{to_branch}"'
        
        # Add commit message if available
        commit_message = action.get('message', '')
        if commit_message:
            base_message += f"\n {commit_message}"
        
        return f"{base_message}\n{formatted_time}"
    
    else:
        return f'"{author}" performed {action_type} action on {formatted_time}'
