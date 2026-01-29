from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
import os
import google.generativeai as genai
import json
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

FIREBASE_CONFIG = {
    'apiKey': os.getenv('FIREBASE_API_KEY'),
    'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
    'projectId': os.getenv('FIREBASE_PROJECT_ID'),
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
    'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
    'appId': os.getenv('FIREBASE_APP_ID'),
    'measurementId': os.getenv('FIREBASE_MEASUREMENT_ID')
}


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login')
def login():
    return render_template('login.html', firebase_config=FIREBASE_CONFIG)


@app.route('/form')
def form():
    return render_template('form.html', firebase_config=FIREBASE_CONFIG)


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', firebase_config=FIREBASE_CONFIG)


@app.route('/api/generate-roadmap', methods=['POST'])
def generate_roadmap():
    try:
        data = request.json
        
        name = data.get('name', '')
        education = data.get('education', '')
        interests = data.get('interests', '')
        skills = data.get('skills', '')
        goals = data.get('goals', '')
        
        prompt = f"""
You are an expert career counselor and roadmap designer. Based on the following user profile, create a detailed, personalized career roadmap.

User Profile:
- Name: {name}
- Education: {education}
- Interests: {interests}
- Current Skills: {skills}
- Career Goals: {goals}

Please analyze this profile and:
1. Identify the most suitable career path that aligns with their interests, skills, and goals
2. Consider current market demand for skills
3. Create a structured learning roadmap with 6-9 phases
4. Each phase should include a title, duration estimate, and 4-6 specific subtopics to learn

Return your response ONLY as a valid JSON object in this exact format (no markdown, no code blocks, just raw JSON):
{{
  "careerPath": "Name of the career path",
  "summary": "Brief 2-3 sentence explanation of why this career suits them",
  "estimatedDuration": "Total time estimate (e.g., '12-18 months')",
  "phases": [
    {{
      "title": "Phase name",
      "duration": "Time estimate (e.g., '2-3 months')",
      "description": "Brief description of what this phase covers",
      "subtopics": [
        "Specific topic 1 to learn",
        "Specific topic 2 to learn",
        "Specific topic 3 to learn",
        "Specific topic 4 to learn"
      ]
    }}
  ]
}}

Make it practical, actionable, and tailored to their specific profile. Focus on modern, in-demand skills.
"""
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        roadmap_data = json.loads(response_text)
        
        roadmap_data['generatedDate'] = datetime.now().isoformat()
        roadmap_data['userProfile'] = {
            'name': name,
            'education': education,
            'interests': interests,
            'skills': skills,
            'goals': goals
        }
        
        return jsonify({
            'success': True,
            'roadmap': roadmap_data
        })
        
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Response text: {response_text}")
        return jsonify({
            'success': False,
            'error': 'Failed to parse roadmap data. Please try again.'
        }), 500
        
    except Exception as e:
        print(f"Error generating roadmap: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        context = data.get('context', {})  
        
        prompt = f"""
You are a friendly and knowledgeable AI career assistant for NextStep, a career guidance platform. 

User Context:
- Career Path: {context.get('careerPath', 'Not specified')}
- Current Phase: {context.get('currentPhase', 'Not specified')}

User Message: {message}

Provide a helpful, encouraging, and specific response. Keep it concise (2-4 sentences) but informative. 
If they ask about learning resources, suggest specific platforms or tools.
If they ask about career transitions, provide actionable advice.
Be supportive and motivational.
"""
        
        response = model.generate_content(prompt)
        
        return jsonify({
            'success': True,
            'response': response.text.strip()
        })
        
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get response. Please try again.'
        }), 500


@app.route('/api/regenerate-roadmap', methods=['POST'])
def regenerate_roadmap():
    try:
        data = request.json
        
        current_career = data.get('currentCareer', '')
        new_interests = data.get('newInterests', '')
        current_skills = data.get('currentSkills', '')
        user_profile = data.get('userProfile', {})
        
        prompt = f"""
You are an expert career transition counselor. A user wants to transition their career path.

Current Situation:
- Current Career Path: {current_career}
- Current Skills: {current_skills}
- New Interests: {new_interests}
- Education: {user_profile.get('education', '')}
- Name: {user_profile.get('name', '')}

Task: Create a TRANSITION roadmap that:
1. Identifies transferable skills from their current path
2. Builds on their existing knowledge
3. Provides a smooth transition to their new career interest
4. Highlights which skills they can reuse vs. need to learn
5. Makes the transition feel achievable and less overwhelming

Return your response ONLY as a valid JSON object in this exact format (no markdown, no code blocks):
{{
  "careerPath": "New career path name",
  "summary": "2-3 sentences explaining the transition strategy and why it's achievable",
  "estimatedDuration": "Realistic transition time estimate",
  "transferableSkills": ["skill1", "skill2", "skill3"],
  "phases": [
    {{
      "title": "Phase name",
      "duration": "Time estimate",
      "description": "Brief description emphasizing what they already know vs. what's new",
      "subtopics": [
        "Topic 1",
        "Topic 2",
        "Topic 3",
        "Topic 4"
      ]
    }}
  ]
}}

Focus on making the transition feel smooth and leveraging their existing expertise.
"""
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        roadmap_data = json.loads(response_text)
        roadmap_data['generatedDate'] = datetime.now().isoformat()
        roadmap_data['isTransition'] = True
        roadmap_data['fromCareer'] = current_career
        
        return jsonify({
            'success': True,
            'roadmap': roadmap_data
        })
        
    except Exception as e:
        print(f"Error regenerating roadmap: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')