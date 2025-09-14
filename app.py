from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime
import os
import tempfile
import random
import requests

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

def call_anthropic_api(prompt, api_key=None):
    """Call Anthropic API directly using requests"""
    if not api_key:
        api_key = "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"
    
    headers = {
        'x-api-key': api_key,
        'content-type': 'application/json',
        'anthropic-version': '2023-06-01'
    }
    
    # Try different model names that might be available
    models_to_try = [
        'claude-3-5-sonnet-20241022',
        'claude-3-sonnet-20240229',
        'claude-3-haiku-20240307',
        'claude-instant-1.2',
        'claude-2.1',
        'claude-2.0'
    ]
    
    for model in models_to_try:
        data = {
            'model': model,
            'max_tokens': 1024,
            'messages': [{'role': 'user', 'content': prompt}]
        }
        
        try:
            response = requests.post('https://api.anthropic.com/v1/messages', 
                                   headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'content': result['content'][0]['text'],
                    'model': model
                }
            elif response.status_code == 404:
                continue  # Try next model
            else:
                print(f"API Error for {model}: {response.status_code} - {response.text}")
                continue
                
        except Exception as e:
            print(f"Request Error for {model}: {e}")
            continue
    
    return {'success': False, 'error': 'No working model found'}

def generate_questions_with_ai(content):
    """Generate questions using Anthropic API or fallback"""
    try:
        prompt = f"Based on the following study material, generate 5 thoughtful questions that test understanding and application. Return only a Python list of strings format:\n\n{content[:2000]}"
        
        result = call_anthropic_api(prompt)
        
        if result['success']:
            output = result['content'].strip()
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
        else:
            print(f"API failed: {result.get('error', 'Unknown error')}")
            return None
        
    except Exception as e:
        print(f"Error generating questions with AI: {e}")
        return None

def grade_answer_with_ai(question, answer, content=""):
    """Grade answer using Anthropic API or fallback"""
    try:
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
        
        result = call_anthropic_api(prompt)
        
        if result['success']:
            output = result['content'].strip()
            print(f"LLM Grading Response: {output}")
            
            # Try to parse JSON response
            try:
                grading_result = json.loads(output)
                return grading_result
            except:
                # Fallback parsing
                return {
                    "score": 7,
                    "feedback": output,
                    "suggestions": "Consider providing more specific examples and details."
                }
        else:
            print(f"API failed: {result.get('error', 'Unknown error')}")
            return None
        
    except Exception as e:
        print(f"Error grading with AI: {e}")
        return None

def generate_fallback_questions(content):
    """Generate smart fallback questions based on content analysis"""
    content_lower = content.lower()
    
    # Biology-related questions
    if any(word in content_lower for word in ['cell', 'biology', 'organism', 'dna', 'protein']):
        return [
            "What is the fundamental unit of life and why is it important?",
            "How do cells maintain their structure and function?",
            "What are the key differences between prokaryotic and eukaryotic cells?",
            "How do cells communicate with each other?",
            "What role do organelles play in cellular function?"
        ]
    # Technology-related questions
    elif any(word in content_lower for word in ['code', 'programming', 'software', 'algorithm', 'data']):
        return [
            "What are the key principles of good software design?",
            "How would you optimize this algorithm for better performance?",
            "What are the potential security implications of this approach?",
            "How would you test this code to ensure reliability?",
            "What are the trade-offs between different implementation approaches?"
        ]
    # General academic questions
    else:
        return [
            "What are the main concepts discussed in this material?",
            "How would you explain this topic to someone unfamiliar with it?",
            "What are the practical applications of this knowledge?",
            "What questions do you still have about this topic?",
            "How does this connect to other concepts you've learned?"
        ]

def grade_answer_fallback(question, answer, content=""):
    """Fallback grading system"""
    answer_lower = answer.lower()
    
    # Base score
    score = 5
    
    # Length-based scoring
    word_count = len(answer.split())
    if word_count > 50:
        score += 2
    elif word_count > 20:
        score += 1
    
    # Quality indicators
    quality_indicators = [
        'because', 'therefore', 'however', 'example', 'specifically', 
        'in other words', 'for instance', 'moreover', 'furthermore',
        'analysis', 'explanation', 'understanding', 'concept'
    ]
    
    quality_count = sum(1 for indicator in quality_indicators if indicator in answer_lower)
    score += min(quality_count, 3)
    
    # Technical depth
    if any(word in answer_lower for word in ['technical', 'implementation', 'algorithm', 'structure']):
        score += 1
    
    # Add some randomness for realism
    score += random.randint(-1, 2)
    score = max(1, min(10, score))
    
    # Generate feedback based on score
    if score >= 9:
        feedback = "Outstanding answer! You demonstrated exceptional understanding with clear explanations, specific examples, and insightful analysis."
        suggestions = "Excellent work! Consider exploring related advanced topics to deepen your knowledge further."
    elif score >= 7:
        feedback = "Very good answer! You showed solid understanding of the concepts with good explanations and examples."
        suggestions = "Great job! Try to add more specific examples or case studies to strengthen your response."
    elif score >= 5:
        feedback = "Good answer! You covered the main points but could benefit from more detailed explanations and examples."
        suggestions = "Good foundation! Consider providing more specific examples and explaining the 'why' behind your points."
    else:
        feedback = "Your answer needs improvement. Try to provide more specific details, examples, and explanations."
        suggestions = "Focus on providing more detailed explanations, specific examples, and connecting concepts together."
    
    return {
        "score": score,
        "feedback": feedback,
        "suggestions": suggestions
    }

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
                
                # Read file content for AI processing
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
    """Generate study questions based on uploaded content using AI"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        if not content:
            return jsonify({
                'success': False,
                'message': 'No content provided for question generation'
            }), 400
        
        print(f"Generating questions for content: {content[:100]}...")
        
        # Try AI first, fallback to smart questions
        ai_questions = generate_questions_with_ai(content)
        
        if ai_questions:
            questions = ai_questions
            source = "AI-Generated (Anthropic)"
            print(f"✅ Generated {len(questions)} questions using Anthropic AI")
        else:
            # Fallback to smart questions
            questions = generate_fallback_questions(content)
            source = "Smart-Generated"
            print(f"⚠️  Using smart fallback questions")
        
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
        
        # Try AI grading first
        ai_result = grade_answer_with_ai(question, answer, content)
        
        if ai_result:
            score = ai_result.get('score', 7)
            feedback = ai_result.get('feedback', 'Good answer!')
            suggestions = ai_result.get('suggestions', 'Keep up the good work!')
            source = "AI-Graded (Anthropic)"
            print(f"✅ Graded using Anthropic AI: {score}/10")
        else:
            # Fallback to smart grading
            fallback_result = grade_answer_fallback(question, answer, content)
            score = fallback_result.get('score', 7)
            feedback = fallback_result.get('feedback', 'Good answer!')
            suggestions = fallback_result.get('suggestions', 'Keep up the good work!')
            source = "Smart-Graded"
            print(f"⚠️  Graded using smart fallback: {score}/10")
        
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
    print("🤖 AI Integration: ENABLED (Anthropic API + Smart Fallback)")
    print("🎤 Ready to help you study with AI!")
    app.run(debug=True, host='0.0.0.0', port=8080)
