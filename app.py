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

def read_file_content(file_path):
    """Read file content as string"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        return f"Error reading file: {e}"

def generate_questions_with_llm(content):
    """Generate questions using the original LLM approach from feature/llm branch"""
    try:
        # Import and use the original LLM integration
        import anthropic
        
        # Use the API key from the feature/llm branch
        client = anthropic.Anthropic(
            api_key="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"
        )
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": f"based on {content[:2000]} give me 3 questions that I have to answer in a python list of string type format. return only a list of text"}
            ]
        )
        
        output = message.content[0].text.strip()
        print(f"LLM Response: {output}")
        
        # Try to parse as Python list
        try:
            questions = eval(output)
            if isinstance(questions, list):
                return questions
        except:
            pass
        
        # Fallback: split by lines and clean up
        questions = [q.strip() for q in output.split('\n') if q.strip()]
        return questions[:5]  # Limit to 5 questions
        
    except Exception as e:
        print(f"Error generating questions with LLM: {e}")
        return None

def grade_answer_with_llm(question, answer, content=""):
    """Grade answer using LLM"""
    try:
        import anthropic
        
        client = anthropic.Anthropic(
            api_key="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"
        )
        
        prompt = f"""
        Question: {question}
        Student Answer: {answer}
        
        Please grade this answer on a scale of 1-10 and provide feedback. Consider:
        - Accuracy of the answer
        - Depth of understanding
        - Use of examples
        - Clarity of explanation
        
        Return your response in this exact JSON format:
        {{
            "score": <number between 1-10>,
            "feedback": "<detailed feedback>",
            "suggestions": "<specific suggestions for improvement>"
        }}
        """
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        
        output = message.content[0].text.strip()
        print(f"LLM Grading Response: {output}")
        
        # Try to parse JSON response
        try:
            result = json.loads(output)
            return result
        except:
            # Fallback parsing
            return {
                "score": 7,
                "feedback": output,
                "suggestions": "Consider providing more specific examples and details."
            }
        
    except Exception as e:
        print(f"Error grading with LLM: {e}")
        return None

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
                
                # Read file content for LLM processing
                content = read_file_content(file_path)
                
                file_info = {
                    'id': len(uploaded_files) + 1,
                    'filename': filename,
                    'file_path': file_path,
                    'content': content,
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

@app.route("/generate_questions", methods=["POST"])
def generate_questions():
    """Generate study questions based on uploaded content using LLM"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        if not content:
            return jsonify({
                'success': False,
                'message': 'No content provided for question generation'
            }), 400
        
        print(f"Generating questions for content: {content[:100]}...")
        
        # Try LLM first, fallback to predefined questions
        llm_questions = generate_questions_with_llm(content)
        
        if llm_questions:
            questions = llm_questions
            source = "AI-Generated"
            print(f"✅ Generated {len(questions)} questions using LLM")
        else:
            # Fallback questions
            questions = [
                "Explain the main concept discussed in your study material.",
                "What are the key points you need to remember?",
                "How would you apply this knowledge in a real-world scenario?",
                "What are the potential challenges or limitations mentioned?",
                "Summarize the most important takeaway from your study material."
            ]
            source = "Predefined"
            print(f"⚠️  Using fallback questions")
        
        return jsonify({
            'success': True,
            'questions': questions,
            'source': source,
            'llm_available': True,
            'message': f'Generated {len(questions)} study questions using {source}'
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
        content = data.get('content', '')
        
        if not question or not answer:
            return jsonify({
                'success': False,
                'message': 'Question and answer are required'
            }), 400
        
        print(f"Grading answer: {answer[:50]}...")
        
        # Try LLM grading first
        llm_result = grade_answer_with_llm(question, answer, content)
        
        if llm_result:
            score = llm_result.get('score', 7)
            feedback = llm_result.get('feedback', 'Good answer!')
            suggestions = llm_result.get('suggestions', 'Keep up the good work!')
            source = "AI-Graded"
            print(f"✅ Graded using LLM: {score}/10")
        else:
            # Fallback to rule-based grading
            import random
            
            score = 5  # Base score
            if len(answer.split()) > 20:
                score += 2
            if len(answer.split()) > 50:
                score += 2
            
            understanding_keywords = ['because', 'therefore', 'however', 'example', 'specifically']
            if any(keyword in answer.lower() for keyword in understanding_keywords):
                score += 1
            
            score += random.randint(-1, 2)
            score = max(1, min(10, score))
            
            if score >= 8:
                feedback = "Excellent answer! You demonstrated a thorough understanding."
            elif score >= 6:
                feedback = "Good answer! Consider adding more specific examples."
            elif score >= 4:
                feedback = "Fair answer. Could benefit from more detailed explanations."
            else:
                feedback = "Your answer needs improvement. Try to provide more specific details."
            
            suggestions = "Consider providing more examples and detailed explanations."
            source = "Rule-Based"
            print(f"⚠️  Graded using fallback: {score}/10")
        
        is_correct = score >= 7
        
        return jsonify({
            'success': True,
            'score': score,
            'is_correct': is_correct,
            'feedback': feedback,
            'suggestions': suggestions,
            'source': source,
            'llm_available': True,
            'message': f'Answer graded successfully using {source}'
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
                    'improvement_trend': [],
                    'llm_usage': 0
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
                'improvement_trend': improvement_trend,
                'llm_available': True
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
    print("🤖 LLM Integration: ENABLED (Claude AI)")
    print("🎤 Ready to help you study with AI!")
    app.run(debug=True, host='0.0.0.0', port=8080)
