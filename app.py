from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime
import os
import tempfile

app = Flask(__name__)
app.config["SECRET_KEY"] = "studyai-secret-key"

# In-memory storage for demo (replace with database in production)
study_sessions = []
uploaded_files = []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_files():
    """Handle file uploads for study materials"""
    try:
        if "files" not in request.files:
            return jsonify({"success": False, "message": "No files uploaded"}), 400
        
        files = request.files.getlist("files")
        uploaded_file_info = []
        
        for file in files:
            if file.filename:
                # Save file temporarily
                filename = file.filename
                file_path = os.path.join(tempfile.gettempdir(), filename)
                file.save(file_path)
                
                file_info = {
                    'id': len(uploaded_files) + 1,
                    'filename': filename,
                    'file_path': file_path,
                    'size': os.path.getsize(file_path),
                    'uploaded_at': datetime.now().isoformat()
                }
                
                uploaded_files.append(file_info)
                uploaded_file_info.append(file_info)
        
        return jsonify({
            'success': True,
            'files': uploaded_file_info,
            'message': f'Successfully uploaded {len(uploaded_file_info)} files'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error uploading files: {str(e)}'
        }), 500

@app.route("/speech_to_text", methods=["POST"])
def speech_to_text():
    """Convert speech to text using browser's built-in speech recognition"""
    try:
        # This endpoint is for future Whisper integration
        # For now, we'll use browser's built-in speech recognition
        return jsonify({
            "success": True,
            "message": "Speech recognition handled by browser"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error processing speech: {str(e)}"
        }), 500

@app.route("/generate_questions", methods=["POST"])
def generate_questions():
    """Generate study questions based on uploaded content"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        if not content:
            return jsonify({
                'success': False,
                'message': 'No content provided for question generation'
            }), 400
        
        # Generate questions based on content (this would be replaced with actual AI)
        questions = [
            "Explain the main concept discussed in your study material.",
            "What are the key points you need to remember?",
            "How would you apply this knowledge in a real-world scenario?",
            "What are the potential challenges or limitations mentioned?",
            "Summarize the most important takeaway from your study material.",
            "What questions do you still have about this topic?",
            "How does this connect to other concepts you've learned?",
            "What practical examples can you think of?",
            "What would you like to explore further about this topic?",
            "How confident do you feel about this material?"
        ]
        
        return jsonify({
            'success': True,
            'questions': questions,
            'message': f'Generated {len(questions)} study questions'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating questions: {str(e)}'
        }), 500

@app.route("/grade_answer", methods=["POST"])
def grade_answer():
    """Grade student's answer using AI"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        answer = data.get('answer', '')
        
        if not question or not answer:
            return jsonify({
                'success': False,
                'message': 'Question and answer are required'
            }), 400
        
        # Simulate AI grading (replace with actual AI model)
        import random
        
        # Basic scoring based on answer length and keywords
        score = 5  # Base score
        
        # Increase score based on answer length (more detailed answers)
        if len(answer.split()) > 20:
            score += 2
        if len(answer.split()) > 50:
            score += 2
        
        # Increase score for certain keywords that indicate understanding
        understanding_keywords = ['because', 'therefore', 'however', 'example', 'specifically', 'in other words']
        if any(keyword in answer.lower() for keyword in understanding_keywords):
            score += 1
        
        # Add some randomness to make it more realistic
        score += random.randint(-1, 2)
        score = max(1, min(10, score))  # Keep between 1-10
        
        is_correct = score >= 7
        
        # Generate feedback based on score
        if score >= 8:
            feedback = "Excellent answer! You demonstrated a thorough understanding of the concept with clear explanations and good examples."
        elif score >= 6:
            feedback = "Good answer! You showed understanding of the main concepts. Consider adding more specific examples to strengthen your response."
        elif score >= 4:
            feedback = "Fair answer. You touched on some key points but could benefit from more detailed explanations and examples."
        else:
            feedback = "Your answer needs improvement. Try to provide more specific details and examples to demonstrate your understanding."
        
        return jsonify({
            'success': True,
            'score': score,
            'is_correct': is_correct,
            'feedback': feedback,
            'message': 'Answer graded successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error grading answer: {str(e)}'
        }), 500

@app.route("/save_session", methods=["POST"])
def save_session():
    """Save study session data"""
    try:
        data = request.get_json()
        
        session = {
            'id': len(study_sessions) + 1,
            'questions': data.get('questions', []),
            'answers': data.get('answers', []),
            'scores': data.get('scores', []),
            'total_score': data.get('total_score', 0),
            'accuracy': data.get('accuracy', 0),
            'created_at': datetime.now().isoformat()
        }
        
        study_sessions.append(session)
        
        return jsonify({
            'success': True,
            'session': session,
            'message': 'Study session saved successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saving session: {str(e)}'
        }), 500

@app.route("/sessions", methods=["GET"])
def get_sessions():
    """Get all study sessions"""
    return jsonify({
        'success': True,
        'sessions': study_sessions
    })

@app.route("/analytics", methods=["GET"])
def get_analytics():
    """Get study analytics"""
    try:
        if not study_sessions:
            return jsonify({
                'success': True,
                'analytics': {
                    'total_sessions': 0,
                    'average_score': 0,
                    'average_accuracy': 0,
                    'total_questions': 0,
                    'improvement_trend': []
                }
            })
        
        total_sessions = len(study_sessions)
        total_questions = sum(len(session.get('questions', [])) for session in study_sessions)
        average_score = sum(session.get('total_score', 0) for session in study_sessions) / total_sessions
        average_accuracy = sum(session.get('accuracy', 0) for session in study_sessions) / total_sessions
        
        # Calculate improvement trend (last 5 sessions)
        recent_sessions = study_sessions[-5:] if len(study_sessions) >= 5 else study_sessions
        improvement_trend = [session.get('accuracy', 0) for session in recent_sessions]
        
        return jsonify({
            'success': True,
            'analytics': {
                'total_sessions': total_sessions,
                'average_score': round(average_score, 2),
                'average_accuracy': round(average_accuracy, 2),
                'total_questions': total_questions,
                'improvement_trend': improvement_trend
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting analytics: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🎓 Starting StudyAI - AI-Powered Study Assistant...")
    print("📱 Open your browser and go to: http://localhost:8080")
    print("🎤 Ready to help you study with AI!")
    app.run(debug=True, host='0.0.0.0', port=8080)
