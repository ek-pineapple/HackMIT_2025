from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime
import os
import tempfile
from dotenv import load_dotenv
import anthropic

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = "studyai-secret-key"

# In-memory storage for demo (replace with database in production)
study_sessions = []
uploaded_files = []

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

llm_client = None
llm_available = False

if ANTHROPIC_API_KEY:
    try:
        llm_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        llm_available = True
        print("🤖 AI Integration: ENABLED (Anthropic Claude AI)")
    except Exception as e:
        print(f"⚠️ LLM not available: {e}")
        print("⚠️ LLM Integration: DISABLED (Fallback mode)")
else:
    print("⚠️ ANTHROPIC_API_KEY not found. LLM Integration: DISABLED (Fallback mode)")

def read_file_content(file_path):
    """Read file content with proper encoding handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e:
            return f"Error reading file: {e}"
    except Exception as e:
        return f"Error reading file: {e}"

def generate_questions_with_ai(content):
    """Generate questions using Anthropic API or fallback"""
    try:
        prompt = f"""Based on the following study material, generate exactly 5 thoughtful questions that test understanding and application.

IMPORTANT: Return ONLY a JSON array of strings, no other text, no explanations, no prefixes.

Study material:
{content[:2000]}

Return format:
["Question 1", "Question 2", "Question 3", "Question 4", "Question 5"]"""
        
        if llm_available and llm_client:
            message = llm_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            output = message.content[0].text.strip()
            print(f"LLM Response: {output}")
            
            # Try to parse as JSON array
            try:
                questions = json.loads(output)
                if isinstance(questions, list) and len(questions) >= 5:
                    return questions[:5]
            except json.JSONDecodeError:
                pass
            
            # Fallback: try to extract questions from text
            lines = [line.strip() for line in output.split('\n') if line.strip()]
            questions = []
            for line in lines:
                if line.startswith('"') and line.endswith('"'):
                    questions.append(line[1:-1])
                elif '?' in line and len(line) > 10:
                    questions.append(line)
            return questions[:5] if questions else None
        else:
            return None
    except Exception as e:
        print(f"Error generating questions with AI: {e}")
        return None

def generate_followup_questions(question, answer, score, content=""):
    """Generate follow-up questions based on the answer quality"""
    try:
        if score >= 8:
            # Good answer - generate deeper questions
            prompt = f"""The student gave a good answer (score: {score}/10) to this question: "{question}"

Generate 3 follow-up questions that test deeper understanding and application. Return ONLY a JSON array of strings.

Study material context: {content[:1000]}

Return format: ["Follow-up 1", "Follow-up 2", "Follow-up 3"]"""
        else:
            # Poor answer - generate clarifying questions
            prompt = f"""The student gave a poor answer (score: {score}/10) to this question: "{question}"

Student's answer: "{answer}"

Generate 3 follow-up questions that help clarify the concept and test basic understanding. Return ONLY a JSON array of strings.

Study material context: {content[:1000]}

Return format: ["Follow-up 1", "Follow-up 2", "Follow-up 3"]"""
        
        if llm_available and llm_client:
            message = llm_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            output = message.content[0].text.strip()
            print(f"Follow-up LLM Response: {output}")
            
            try:
                questions = json.loads(output)
                if isinstance(questions, list):
                    return questions[:3]
            except json.JSONDecodeError:
                pass
            
            # Fallback parsing
            lines = [line.strip() for line in output.split('\n') if line.strip()]
            questions = []
            for line in lines:
                if line.startswith('"') and line.endswith('"'):
                    questions.append(line[1:-1])
                elif '?' in line and len(line) > 10:
                    questions.append(line)
            return questions[:3] if questions else None
        else:
            return None
    except Exception as e:
        print(f"Error generating follow-up questions: {e}")
        return None

def grade_answer_with_ai(question, answer, content=""):
    """Grade answer using Anthropic API or fallback"""
    try:
        prompt = f"""Grade this student's answer on a scale of 1-10 and provide feedback.

Question: {question}
Student Answer: {answer}
Study Material Context: {content[:1000]}

Return ONLY a JSON object with this exact format:
{{
    "score": <number between 1-10>,
    "feedback": "<detailed feedback>",
    "suggestions": "<improvement suggestions>"
}}"""
        
        if llm_available and llm_client:
            message = llm_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            output = message.content[0].text.strip()
            print(f"Grading LLM Response: {output}")
            
            try:
                result = json.loads(output)
                if isinstance(result, dict) and 'score' in result:
                    return result
            except json.JSONDecodeError:
                pass
        
        # Fallback grading
        return simulate_ai_grading(question, answer)
    except Exception as e:
        print(f"Error grading with AI: {e}")
        return simulate_ai_grading(question, answer)

def simulate_ai_grading(question, answer):
    """Fallback grading system"""
    score = 7  # Default score
    feedback = "Good attempt! Your answer shows understanding of the topic."
    suggestions = "Try to provide more specific examples and details."
    
    # Simple keyword-based scoring
    if len(answer) < 20:
        score = 3
        feedback = "Your answer is too brief. Please provide more detail."
        suggestions = "Expand your answer with specific examples and explanations."
    elif any(word in answer.lower() for word in ['i don\'t know', 'not sure', 'maybe']):
        score = 4
        feedback = "It's okay to be uncertain, but try to apply what you know."
        suggestions = "Use the study material to form a more confident answer."
    elif len(answer) > 100:
        score = 8
        feedback = "Excellent detailed answer! You've shown good understanding."
        suggestions = "Keep up the great work with detailed explanations!"
    
    return {
        "score": score,
        "feedback": feedback,
        "suggestions": suggestions
    }

def generate_fallback_questions(content):
    """Generate fallback questions when AI is not available"""
    questions = [
        "What are the main concepts discussed in this material?",
        "How would you explain the key points to someone else?",
        "What examples can you think of that relate to this topic?",
        "What questions do you still have about this material?",
        "How does this information connect to what you already know?"
    ]
    return questions

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_files():
    """Handle file uploads"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'message': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        uploaded_files_data = []
        
        for file in files:
            if file.filename == '':
                continue
                
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp_file:
                file.save(tmp_file.name)
                
                # Read content
                content = read_file_content(tmp_file.name)
                
                # Store file info
                file_data = {
                    'id': len(uploaded_files) + 1,
                    'filename': file.filename,
                    'size': len(content),
                    'content': content,
                    'file_path': tmp_file.name,
                    'uploaded_at': datetime.now().isoformat()
                }
                
                uploaded_files.append(file_data)
                uploaded_files_data.append(file_data)
        
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {len(uploaded_files_data)} files',
            'files': uploaded_files_data
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
            print(f"⚠️ Using smart fallback questions")
        
        return jsonify({
            'success': True,
            'questions': questions,
            'source': source,
            'llm_available': llm_available,
            'message': f'Generated {len(questions)} study questions using {source}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating questions: {str(e)}'
        }), 500

@app.route("/generate_followup", methods=["POST"])
def generate_followup():
    """Generate follow-up questions based on answer quality"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        answer = data.get('answer', '')
        score = data.get('score', 0)
        content = data.get('content', '')
        
        if not question or not answer:
            return jsonify({
                'success': False,
                'message': 'Question and answer are required'
            }), 400
        
        print(f"Generating follow-up questions for score: {score}/10")
        
        followup_questions = generate_followup_questions(question, answer, score, content)
        
        if followup_questions:
            source = "AI-Generated Follow-ups"
            print(f"✅ Generated {len(followup_questions)} follow-up questions")
        else:
            # Fallback follow-up questions
            if score >= 8:
                followup_questions = [
                    "Can you provide a real-world example of this concept?",
                    "How would you apply this knowledge in a different context?",
                    "What are the implications of this concept?"
                ]
            else:
                followup_questions = [
                    "Can you explain this concept in simpler terms?",
                    "What part of this topic would you like to review?",
                    "How does this relate to the main study material?"
                ]
            source = "Smart Follow-ups"
            print(f"⚠️ Using smart follow-up questions")
        
        return jsonify({
            'success': True,
            'questions': followup_questions,
            'source': source,
            'llm_available': llm_available,
            'message': f'Generated {len(followup_questions)} follow-up questions'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating follow-up questions: {str(e)}'
        }), 500

@app.route("/grade_answer", methods=["POST"])
def grade_answer():
    """Grade student answers using AI"""
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
        
        # Grade using AI or fallback
        grade_result = grade_answer_with_ai(question, answer, content)
        
        score = grade_result.get('score', 7)
        feedback = grade_result.get('feedback', 'Good attempt!')
        suggestions = grade_result.get('suggestions', 'Keep practicing!')
        
        is_correct = score >= 7
        
        source = "AI-Graded (Anthropic)" if llm_available else "Rule-Based"
        print(f"✅ Graded using {source}: {score}/10")
        
        return jsonify({
            'success': True,
            'score': score,
            'is_correct': is_correct,
            'feedback': feedback,
            'suggestions': suggestions,
            'message': 'Answer graded successfully',
            'source': source,
            'llm_available': llm_available
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
        
        session_data = {
            'id': len(study_sessions) + 1,
            'timestamp': datetime.now().isoformat(),
            'questions': data.get('questions', []),
            'answers': data.get('answers', []),
            'scores': data.get('scores', []),
            'total_score': data.get('total_score', 0),
            'accuracy': data.get('accuracy', 0)
        }
        
        study_sessions.append(session_data)
        
        return jsonify({
            'success': True,
            'message': 'Session saved successfully',
            'session_id': session_data['id']
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
                    'sessions': []
                }
            })
        
        total_sessions = len(study_sessions)
        total_score = sum(session.get('total_score', 0) for session in study_sessions)
        total_accuracy = sum(session.get('accuracy', 0) for session in study_sessions)
        
        analytics = {
            'total_sessions': total_sessions,
            'average_score': total_score / total_sessions if total_sessions > 0 else 0,
            'average_accuracy': total_accuracy / total_sessions if total_sessions > 0 else 0,
            'sessions': study_sessions[-10:]  # Last 10 sessions
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting analytics: {str(e)}'
        }), 500

if __name__ == "__main__":
    print("🎓 Starting StudyAI - AI-Powered Study Assistant...")
    print("📱 Open your browser and go to: http://localhost:8080")
    print("🎤 Ready to help you study with AI!")
    app.run(host="0.0.0.0", port=8080, debug=True)
