from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import uuid
import json
import PyPDF2
import docx
from werkzeug.utils import secure_filename
from openai import OpenAI
import requests
import json
import os
from urllib.parse import urlencode

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize Kluster AI client
client = OpenAI(
    api_key="fdd5642c-cba8-4c2b-842f-9bd4ce775011",
    base_url="https://api.kluster.ai/v1"
)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path):
    """Extract text from different file formats"""
    file_extension = file_path.split('.')[-1].lower()
    
    if file_extension == 'pdf':
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text() or ""
        except Exception as e:
            print(f"Error extracting PDF text: {str(e)}")
        return text
    
    elif file_extension == 'docx':
        try:
            doc = docx.Document(file_path)
            return " ".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            print(f"Error extracting DOCX text: {str(e)}")
            return ""
    
    elif file_extension == 'txt':
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        except Exception as e:
            print(f"Error extracting TXT text: {str(e)}")
            return ""
    
    return ""

def analyze_resume(file_path):
    """Use Kluster AI API to analyze the resume"""
    try:
        # Extract text from the resume
        resume_text = extract_text_from_file(file_path)
        
        print(f"Extracted text length: {len(resume_text)}")
        
        if not resume_text or len(resume_text.strip()) < 50:
            print("Insufficient text extracted from resume")
            return default_analysis()
        
        print("Sending request to Kluster AI API...")
        
        # Prepare the system and user messages
        # Update the user message to request line suggestions
        messages = [
            {"role": "system", "content": "You are a professional resume analyzer. Provide detailed feedback on resumes in JSON format."},
            {"role": "user", "content": f"""
                Analyze the following resume and provide detailed feedback:
                
                {resume_text[:3500]}
                
                Provide the analysis in the following JSON format:
                {{
                    "score": (a number between 0-100 representing overall quality),
                    "feedback": {{
                        "strengths": [list of 3-5 strengths],
                        "improvements": [list of 3-5 areas for improvement]
                    }},
                    "keywords_detected": [list of important keywords found in the resume],
                    "missing_keywords": [list of suggested keywords that could improve the resume],
                    "suggested_improvements": {{
                        "original_lines": [list of problematic lines from the resume],
                        "suggested_lines": [list of improved versions of those lines]
                    }}
                }}
                
                Only respond with the JSON, no additional text.
            """}
        ]
        
        # Call Kluster AI API using the OpenAI client format
        completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3-0324",
            max_completion_tokens=8000,
            temperature=2,
            top_p=1,
            messages=messages
        )
        
        print("Received response from Kluster AI API")
        
        # Extract and parse the JSON response
        ai_response = completion.choices[0].message.content.strip()
        print(f"AI response: {ai_response[:100]}...")  # Print first 100 chars of response
        
        # Find the JSON part in the response (in case the AI added extra text)
        json_start = ai_response.find('{')
        json_end = ai_response.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = ai_response[json_start:json_end]
            try:
                analysis = json.loads(json_str)
                print("Successfully parsed JSON response")
                return analysis
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")
                print(f"JSON string: {json_str[:100]}...")
                return default_analysis()
        else:
            print("Failed to parse JSON from AI response")
            return default_analysis()
            
    except Exception as e:
        print(f"Error in AI analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return default_analysis()

def default_analysis():
    """Fallback analysis if AI fails"""
    return {
        "score": 70,
        "feedback": {
            "strengths": [
                "Resume structure is clear",
                "Contains relevant information",
                "Good formatting"
            ],
            "improvements": [
                "Consider adding more specific achievements",
                "Quantify your accomplishments",
                "Tailor resume to specific job descriptions"
            ]
        },
        "keywords_detected": ["Experience", "Education", "Skills"],
        "missing_keywords": ["Leadership", "Project Management", "Results-oriented"],
        "suggested_improvements": {
            "original_lines": [
                "Managed team projects",
                "Responsible for customer service",
                "Good communication skills"
            ],
            "suggested_lines": [
                "Led 5-person team to deliver $200K project under budget",
                "Achieved 98% customer satisfaction rating while handling 50+ daily inquiries",
                "Delivered 10+ presentations to senior management, resulting in successful project approvals"
            ]
        }
    }

# Ensure examples directory exists
os.makedirs('static/examples', exist_ok=True)

# Copy the sample PDF to the examples directory
import shutil
try:
    shutil.copy("C:\\Users\\tiwar\\Downloads\\sample.pdf", "static/examples/example_resume.pdf")
    print("Sample resume copied successfully")
except Exception as e:
    print(f"Error copying sample resume: {str(e)}")

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/example-resume')
def example_resume():
    # Instead of just sending the file, render a template that displays it
    return render_template('example_resume.html')

@app.route('/resume-format')
def resume_format():
    # Return a resume format guide
    return send_from_directory('static/examples', 'resume_format_guide.pdf')

@app.route('/analyzer')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'resume' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['resume']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        # Create unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save the file
        file.save(file_path)
        
        print(f"File saved at: {file_path}")
        
        # Analyze the resume
        analysis = analyze_resume(file_path)
        
        # Check if we're getting the default analysis
        is_default = (analysis == default_analysis())
        print(f"Using default analysis: {is_default}")
        
        return jsonify({
            "success": True,
            "filename": unique_filename,
            "analysis": analysis,
            "is_default_analysis": is_default
        })
    
    return jsonify({"error": "File type not allowed"}), 400

def compare_resumes(file_path1, file_path2):
    """Compare two resumes using Kluster AI API"""
    try:
        # Extract text from both resumes
        resume_text1 = extract_text_from_file(file_path1)
        resume_text2 = extract_text_from_file(file_path2)
        
        print(f"Extracted text lengths: Resume 1: {len(resume_text1)}, Resume 2: {len(resume_text2)}")
        
        if not resume_text1 or not resume_text2 or len(resume_text1.strip()) < 50 or len(resume_text2.strip()) < 50:
            print("Insufficient text extracted from one or both resumes")
            return default_comparison()
        
        print("Sending comparison request to Kluster AI API...")
        
        messages = [
            {"role": "system", "content": "You are a professional resume analyzer. Compare two resumes and provide detailed comparison in JSON format."},
            {"role": "user", "content": f"""
                Compare the following two resumes and provide detailed analysis:
                
                Resume 1:
                {resume_text1[:3000]}
                
                Resume 2:
                {resume_text2[:3000]}
                
                Provide the comparison in the following JSON format:
                {{
                    "overall_comparison": {{
                        "stronger_resume": "1 or 2",
                        "score_resume1": (number between 0-100),
                        "score_resume2": (number between 0-100)
                    }},
                    "key_differences": {{
                        "experience": [list of main differences in experience],
                        "skills": [list of unique skills in each resume],
                        "education": [list of differences in education],
                        "achievements": [list of notable achievements comparison]
                    }},
                    "recommendations": {{
                        "resume1": [list of improvements for resume 1],
                        "resume2": [list of improvements for resume 2]
                    }}
                }}
                
                Only respond with the JSON, no additional text.
            """}
        ]
        
        completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3-0324",
            max_completion_tokens=4000,
            temperature=0.6,
            top_p=1,
            messages=messages
        )
        
        print("Received response from Kluster AI API")
        
        # Extract and parse the JSON response
        ai_response = completion.choices[0].message.content.strip()
        print(f"AI response: {ai_response[:100]}...")  # Print first 100 chars of response
        
        # Find the JSON part in the response (in case the AI added extra text)
        json_start = ai_response.find('{')
        json_end = ai_response.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = ai_response[json_start:json_end]
            try:
                comparison = json.loads(json_str)
                print("Successfully parsed JSON response")
                return comparison
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")
                print(f"JSON string: {json_str[:100]}...")
                return default_comparison()
        else:
            print("Failed to parse JSON from AI response")
            return default_comparison()
        
    except Exception as e:
        print(f"Error in resume comparison: {str(e)}")
        import traceback
        traceback.print_exc()
        return default_comparison()

def default_comparison():
    """Fallback comparison if AI fails"""
    return {
        "overall_comparison": {
            "stronger_resume": "Equal",
            "score_resume1": 75,
            "score_resume2": 75
        },
        "key_differences": {
            "experience": [
                "Both resumes have similar experience levels",
                "Resume formats differ slightly"
            ],
            "skills": [
                "Skills sections contain different emphasis",
                "Technical skill presentation varies"
            ],
            "education": [
                "Education sections are comparable"
            ],
            "achievements": [
                "Achievement presentation differs between resumes"
            ]
        },
        "recommendations": {
            "resume1": [
                "Add more quantifiable achievements",
                "Enhance skills section with more specific technologies",
                "Include more action verbs in experience descriptions",
                "Consider adding a professional summary",
                "Tailor resume more specifically to target position"
            ],
            "resume2": [
                "Improve formatting for better readability",
                "Add more specific project details",
                "Quantify achievements with numbers and percentages",
                "Consider reorganizing sections for better flow",
                "Add more keywords relevant to the industry"
            ]
        }
    }

@app.route('/compare')
def compare_page():
    """Render the resume comparison page"""
    return render_template('compare.html')

@app.route('/compare', methods=['POST'])
def compare():
    if 'resume1' not in request.files or 'resume2' not in request.files:
        return jsonify({"error": "Two resumes are required"}), 400
    
    file1 = request.files['resume1']
    file2 = request.files['resume2']
    
    if file1.filename == '' or file2.filename == '':
        return jsonify({"error": "Both resumes must be selected"}), 400
    
    if not (allowed_file(file1.filename) and allowed_file(file2.filename)):
        return jsonify({"error": "Invalid file type"}), 400
    
    # Save both files
    filename1 = secure_filename(file1.filename)
    filename2 = secure_filename(file2.filename)
    unique_filename1 = f"{uuid.uuid4()}_{filename1}"
    unique_filename2 = f"{uuid.uuid4()}_{filename2}"
    
    file_path1 = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename1)
    file_path2 = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename2)
    
    file1.save(file_path1)
    file2.save(file_path2)
    
    # Compare the resumes
    comparison = compare_resumes(file_path1, file_path2)
    
    return jsonify({
        "success": True,
        "comparison": comparison
    })

@app.route('/plagiarism')
def plagiarism_page():
    """Render the plagiarism checker page"""
    return render_template('plagiarism.html')

@app.route('/check-plagiarism', methods=['POST'])
def check_plagiarism():
    """Check resume for plagiarism"""
    if 'resume' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['resume']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    # Save the file
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)

    # Extract text from the resume
    resume_text = extract_text_from_file(file_path)

    if not resume_text or len(resume_text.strip()) < 50:
        return jsonify({"error": "Insufficient text extracted from resume"}), 400

    # Use AI to check for plagiarism
    try:
        messages = [
            {"role": "system", "content": "You are a plagiarism detection expert. Analyze the resume for potential plagiarism and provide detailed feedback."},
            {"role": "user", "content": f"""
                Analyze the following resume for potential plagiarism:

                {resume_text[:3500]}

                Provide the analysis in the following JSON format:
                {{
                    "score": (a number between 0-100 representing plagiarism percentage),
                    "assessment": "Overall assessment of plagiarism likelihood",
                    "sections": [
                        {{
                            "text": "potentially plagiarized text",
                            "similarity": (percentage of similarity),
                            "source": "possible source if identifiable"
                        }}
                    ],
                    "recommendations": [list of recommendations to improve originality]
                }}

                Only respond with the JSON, no additional text.
            """}
        ]

        completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3-0324",
            max_completion_tokens=4000,
            temperature=0.6,
            top_p=1,
            messages=messages
        )

        ai_response = completion.choices[0].message.content.strip()

        # Parse JSON response
        json_start = ai_response.find('{')
        json_end = ai_response.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = ai_response[json_start:json_end]
            try:
                results = json.loads(json_str)
                return jsonify({"success": True, "results": results})
            except json.JSONDecodeError:
                return jsonify({"error": "Failed to parse AI response"}), 500
        else:
            return jsonify({"error": "Invalid AI response format"}), 500

    except Exception as e:
        print(f"Error in plagiarism check: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to check for plagiarism"}), 500

# Add these imports at the top if not already present
import tempfile
import zipfile
from flask import session, redirect, url_for, flash

# Add this to your app configuration
app.secret_key = 'your_secret_key_here'  # Replace with a secure random key

# Update the linkedin_import route to handle both OAuth and file upload
@app.route('/linkedin-import')
def linkedin_import():
    """Handle LinkedIn profile import page"""
    # Check if LinkedIn data is in the session (either from OAuth or file upload)
    linkedin_data = session.get('linkedin_data')
    linkedin_profile = session.get('linkedin_profile')
    
    # Default profile info structure
    profile_info = {
        'name': 'John Smith',
        'headline': 'Senior Software Engineer at Tech Company',
        'email': 'john.smith@example.com',
        'phone': '(555) 123-4567',
        'location': 'San Francisco, CA',
        'summary': 'Experienced software engineer with 8+ years of experience in full-stack development. Passionate about creating scalable web applications and solving complex problems.',
        'experience': [
            {
                'company': 'Tech Company Inc.',
                'title': 'Senior Software Engineer',
                'startDate': 'January 2020',
                'endDate': 'Present',
                'description': '- Led development of company\'s flagship product\n- Managed a team of 5 developers\n- Implemented CI/CD pipeline reducing deployment time by 40%\n- Optimized database queries improving performance by 60%'
            },
            {
                'company': 'Previous Company LLC',
                'title': 'Software Developer',
                'startDate': 'June 2017',
                'endDate': 'December 2019',
                'description': '- Developed and maintained web applications using React and Node.js\n- Collaborated with UX designers to implement responsive designs\n- Reduced bug count by 30% through implementation of unit testing'
            }
        ],
        'education': [
            {
                'school': 'University of Technology',
                'degree': 'Bachelor of Science in Computer Science',
                'startDate': '2013',
                'endDate': '2017'
            }
        ],
        'skills': ['JavaScript', 'React', 'Node.js', 'Python', 'AWS', 'Docker', 'Git', 'CI/CD', 'Agile Methodologies', 'Team Leadership', 'Problem Solving']
    }
    
    # If we have LinkedIn data from file upload, process it
    if linkedin_data:
        # Extract profile information from the uploaded data
        if 'profile' in linkedin_data:
            profile = linkedin_data['profile']
            if 'firstName' in profile and 'lastName' in profile:
                profile_info['name'] = f"{profile.get('firstName', '')} {profile.get('lastName', '')}"
            profile_info['headline'] = profile.get('headline', '')
            profile_info['summary'] = profile.get('summary', '')
            
            # Extract location
            if 'geoLocation' in profile and 'city' in profile['geoLocation']:
                profile_info['location'] = f"{profile['geoLocation'].get('city', '')}, {profile['geoLocation'].get('state', '')}"
        
        # Extract experience information
        if 'positions' in linkedin_data:
            positions = linkedin_data['positions']
            if 'elements' in positions:
                profile_info['experience'] = []
                for position in positions['elements']:
                    exp = {
                        'company': position.get('companyName', ''),
                        'title': position.get('title', ''),
                        'startDate': '',
                        'endDate': '',
                        'description': position.get('description', '')
                    }
                    
                    # Format dates
                    if 'startDate' in position:
                        start_month = position['startDate'].get('month', '')
                        start_year = position['startDate'].get('year', '')
                        if start_month and start_year:
                            exp['startDate'] = f"{start_month}/{start_year}"
                        elif start_year:
                            exp['startDate'] = str(start_year)
                    
                    if 'endDate' in position:
                        end_month = position['endDate'].get('month', '')
                        end_year = position['endDate'].get('year', '')
                        if end_month and end_year:
                            exp['endDate'] = f"{end_month}/{end_year}"
                        elif end_year:
                            exp['endDate'] = str(end_year)
                    else:
                        exp['endDate'] = 'Present'
                    
                    profile_info['experience'].append(exp)
        
        # Extract education information
        if 'education' in linkedin_data:
            education = linkedin_data['education']
            if 'elements' in education:
                profile_info['education'] = []
                for edu in education['elements']:
                    education_item = {
                        'school': edu.get('schoolName', ''),
                        'degree': edu.get('degreeName', ''),
                        'field': edu.get('fieldOfStudy', ''),
                        'startDate': '',
                        'endDate': ''
                    }
                    
                    # Format dates
                    if 'startDate' in edu:
                        education_item['startDate'] = str(edu['startDate'].get('year', ''))
                    
                    if 'endDate' in edu:
                        education_item['endDate'] = str(edu['endDate'].get('year', ''))
                    
                    profile_info['education'].append(education_item)
        
        # Extract skills
        if 'skills' in linkedin_data:
            skills = linkedin_data['skills']
            if 'elements' in skills:
                profile_info['skills'] = []
                for skill in skills['elements']:
                    profile_info['skills'].append(skill.get('name', ''))
    
    # If we have LinkedIn profile data from OAuth, process it
    elif linkedin_profile:
        # Extract basic profile info
        profile_info['name'] = f"{linkedin_profile.get('localizedFirstName', '')} {linkedin_profile.get('localizedLastName', '')}"
        
        # Extract email if available
        linkedin_email = session.get('linkedin_email')
        if linkedin_email and 'elements' in linkedin_email and linkedin_email['elements']:
            email_element = linkedin_email['elements'][0]
            if 'handle~' in email_element and 'emailAddress' in email_element['handle~']:
                profile_info['email'] = email_element['handle~']['emailAddress']
    
    return render_template('linkedin_import.html', profile_info=profile_info)

# Add a new route to handle LinkedIn data file upload
@app.route('/linkedin-upload', methods=['POST'])
def linkedin_upload():
    """Handle LinkedIn data export upload"""
    if 'linkedinFile' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['linkedinFile']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.zip'):
        # Create a temporary directory to extract the ZIP file
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save the uploaded file to the temp directory
            zip_path = os.path.join(temp_dir, secure_filename(file.filename))
            file.save(zip_path)
            
            try:
                # Extract the ZIP file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Parse the LinkedIn data
                profile_data = {}
                
                # Try to find and parse the profile.json file
                profile_json_path = os.path.join(temp_dir, 'Profile.json')
                if os.path.exists(profile_json_path):
                    with open(profile_json_path, 'r', encoding='utf-8') as f:
                        profile_json = json.load(f)
                        profile_data['profile'] = profile_json
                
                # Try to find and parse the positions.json file
                positions_json_path = os.path.join(temp_dir, 'Positions.json')
                if os.path.exists(positions_json_path):
                    with open(positions_json_path, 'r', encoding='utf-8') as f:
                        positions_json = json.load(f)
                        profile_data['positions'] = positions_json
                
                # Try to find and parse the education.json file
                education_json_path = os.path.join(temp_dir, 'Education.json')
                if os.path.exists(education_json_path):
                    with open(education_json_path, 'r', encoding='utf-8') as f:
                        education_json = json.load(f)
                        profile_data['education'] = education_json
                
                # Try to find and parse the skills.json file
                skills_json_path = os.path.join(temp_dir, 'Skills.json')
                if os.path.exists(skills_json_path):
                    with open(skills_json_path, 'r', encoding='utf-8') as f:
                        skills_json = json.load(f)
                        profile_data['skills'] = skills_json
                
                # Store the parsed data in the session
                session['linkedin_data'] = profile_data
                
                return jsonify({'success': True, 'redirect': url_for('linkedin_import')}), 200
            except Exception as e:
                print(f"Error processing LinkedIn data: {str(e)}")
                return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file format. Please upload a LinkedIn data export ZIP file.'}), 400

@app.route('/linkedin-auth')
def linkedin_auth():
    """Initiate LinkedIn OAuth flow"""
    # Create the authorization URL
    params = {
        'response_type': 'code',
        'client_id': LINKEDIN_CLIENT_ID,
        'redirect_uri': LINKEDIN_REDIRECT_URI,
        'state': os.urandom(16).hex(),  # Random state to prevent CSRF
        'scope': LINKEDIN_SCOPE
    }
    
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    return redirect(auth_url)

@app.route('/linkedin-callback')
def linkedin_callback():
    """Handle LinkedIn OAuth callback"""
    # Get the authorization code from the request
    code = request.args.get('code')
    
    if not code:
        flash('LinkedIn authorization failed', 'danger')
        return redirect(url_for('linkedin_import'))
    
    # Exchange the authorization code for an access token
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    token_payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': LINKEDIN_REDIRECT_URI,
        'client_id': LINKEDIN_CLIENT_ID,
        'client_secret': LINKEDIN_CLIENT_SECRET
    }
    
    token_response = requests.post(token_url, data=token_payload)
    token_data = token_response.json()
    
    if 'access_token' not in token_data:
        flash('Failed to obtain LinkedIn access token', 'danger')
        return redirect(url_for('linkedin_import'))
    
    access_token = token_data['access_token']
    
    # Fetch user profile data
    profile_url = "https://api.linkedin.com/v2/me"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Restli-Protocol-Version': '2.0.0'
    }
    
    profile_response = requests.get(profile_url, headers=headers)
    profile_data = profile_response.json()
    
    # Fetch email address
    email_url = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"
    email_response = requests.get(email_url, headers=headers)
    email_data = email_response.json()
    
    # Store the profile data in the session
    session['linkedin_profile'] = profile_data
    session['linkedin_email'] = email_data
    
    # Redirect to the LinkedIn import page
    flash('LinkedIn profile successfully imported!', 'success')
    return redirect(url_for('linkedin_import'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)