from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import google.generativeai as genai
import PIL.Image
import shutil

app = Flask(__name__)
GEMINI_API_KEY='AIzaSyDu7KQWy4dJT-3HLFtOkLJylP-yZs-ENBw'

if GEMINI_API_KEY is None:
    raise ValueError("API key is not set in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate-test-cases', methods=['POST'])
def generate_test_cases():
    context = request.form.get('context')
    files = request.files.getlist('screenshots')
    
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400

    saved_files = save_files(files)
    print(saved_files)
    api_response = generate_test_cases_with_gemini(context, saved_files)
    
    return jsonify(api_response)

prompt_template = """
    You are an advanced AI model that generates detailed test cases for UI functionality based on input images. I am uploading multiple UI images that need to be tested, and I expect you to create a detailed, step-by-step guide to test each functionality depicted in the images.

    For each image, please follow this format to create test cases:

    1. *Description*: Explain what this test case is about and the purpose of testing the UI element.
    2. *Pre-conditions*: List the necessary setup or conditions that must be met before starting the test.
    3. *Testing Steps*: Provide clear, numbered, step-by-step instructions on how to carry out the test for that specific image or UI functionality.
    4. *Expected Result*: Clearly state what the outcome should be if the feature works as expected.

    ### Example Output:

    {{
      "testCases": [
        {{
          "testCase": {{
            "Description": "Test the 'Login' button functionality on the login screen.",
            "Pre-conditions": [
              "User should be logged out.",
              "User should have a valid username and password."
            ],
            "Testing Steps": [
              "1. Open the application and navigate to the login screen.",
              "2. Enter the valid username and password into their respective fields.",
              "3. Click the 'Login' button."
            ],
            "Expected Result": "The user should be successfully logged in and redirected to the dashboard page."
          }}
        }},
        {{
          "testCase": {{
            "Description": "Test the search bar functionality on the homepage.",
            "Pre-conditions": [
              "User should be logged in.",
              "There should be data available in the database for search."
            ],
            "Testing Steps": [
              "1. Navigate to the homepage.",
              "2. Enter a search query into the search bar.",
              "3. Click the 'Search' button or press 'Enter'."
            ],
            "Expected Result": "Relevant search results should be displayed based on the search query."
          }}
        }}
      ]
    }}
    """

def save_files(files):
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        shutil.rmtree(app.config['UPLOAD_FOLDER'])  
    os.makedirs(app.config['UPLOAD_FOLDER'])  

    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            saved_files.append(file_path)  
    return saved_files

def generate_test_cases_with_gemini(context, image_paths):
    try:
        images = [PIL.Image.open(image_path) for image_path in image_paths]
        print(context)
        full_prompt = f"{prompt_template}\n\n### Context provided by the user:\n{context}"
        
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
      
        response = model.generate_content([full_prompt, *images])  

        print(response.text)
        return {"response": response.text}
    except Exception as e:
        return {"error": str(e)}


if __name__ == '__main__':
    app.run(debug=True)
