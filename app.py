from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-here"

# In-memory storage for demo (replace with database in production)
entries = []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/speech", methods=["POST"])
def process_speech():
    try:
        data = request.get_json()
        transcript = data.get('transcript', '')
        
        if transcript:
            # Process the speech transcript
            entry = {
                'id': len(entries) + 1,
                'text': transcript,
                'timestamp': datetime.now().isoformat(),
                'type': 'voice',
                'word_count': len(transcript.split()),
                'topics': extract_topics(transcript)
            }
            
            entries.append(entry)
            
            return jsonify({
                'success': True,
                'entry': entry,
                'message': 'Speech processed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No transcript provided'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing speech: {str(e)}'
        }), 500

@app.route("/entries", methods=["GET"])
def get_entries():
    """Get all journal entries"""
    return jsonify({
        'success': True,
        'entries': entries
    })

@app.route("/entries", methods=["POST"])
def save_entry():
    """Save a new journal entry"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        entry_type = data.get('type', 'text')
        
        if text:
            entry = {
                'id': len(entries) + 1,
                'text': text,
                'timestamp': datetime.now().isoformat(),
                'type': entry_type,
                'word_count': len(text.split()),
                'topics': extract_topics(text)
            }
            
            entries.append(entry)
            
            return jsonify({
                'success': True,
                'entry': entry,
                'message': 'Entry saved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No text provided'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saving entry: {str(e)}'
        }), 500

@app.route("/analytics", methods=["GET"])
def get_analytics():
    """Get analytics data for the journal entries"""
    try:
        if not entries:
            return jsonify({
                'success': True,
                'analytics': {
                    'total_entries': 0,
                    'total_words': 0,
                    'avg_words_per_entry': 0,
                    'entries_by_type': {},
                    'entries_by_date': {},
                    'top_topics': []
                }
            })
        
        # Calculate analytics
        total_entries = len(entries)
        total_words = sum(entry.get('word_count', 0) for entry in entries)
        avg_words = total_words / total_entries if total_entries > 0 else 0
        
        # Entries by type
        entries_by_type = {}
        for entry in entries:
            entry_type = entry.get('type', 'unknown')
            entries_by_type[entry_type] = entries_by_type.get(entry_type, 0) + 1
        
        # Entries by date
        entries_by_date = {}
        for entry in entries:
            date = entry['timestamp'][:10]  # YYYY-MM-DD
            entries_by_date[date] = entries_by_date.get(date, 0) + 1
        
        # Top topics
        all_topics = []
        for entry in entries:
            all_topics.extend(entry.get('topics', []))
        
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return jsonify({
            'success': True,
            'analytics': {
                'total_entries': total_entries,
                'total_words': total_words,
                'avg_words_per_entry': round(avg_words, 2),
                'entries_by_type': entries_by_type,
                'entries_by_date': entries_by_date,
                'top_topics': top_topics
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting analytics: {str(e)}'
        }), 500

def extract_topics(text):
    """Simple topic extraction based on keywords"""
    tech_keywords = {
        'work': ['work', 'job', 'office', 'meeting', 'project', 'deadline', 'client'],
        'coding': ['code', 'programming', 'debug', 'bug', 'feature', 'git', 'commit', 'pull request'],
        'learning': ['learn', 'study', 'course', 'tutorial', 'book', 'documentation'],
        'health': ['gym', 'exercise', 'workout', 'run', 'walk', 'health', 'sleep'],
        'social': ['friend', 'family', 'party', 'dinner', 'hangout', 'social'],
        'travel': ['travel', 'trip', 'vacation', 'flight', 'hotel', 'destination'],
        'hobby': ['hobby', 'game', 'music', 'movie', 'read', 'art', 'craft']
    }
    
    text_lower = text.lower()
    found_topics = []
    
    for topic, keywords in tech_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            found_topics.append(topic)
    
    return found_topics

if __name__ == '__main__':
    print("🚀 Starting Voice Journal App...")
    print("📱 Open your browser and go to: http://localhost:8080")
    print("🎤 Ready to record your thoughts!")
    app.run(debug=True, host='0.0.0.0', port=8080)
