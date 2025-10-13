from flask import Flask, render_template, request, jsonify
from mangum import Mangum
import google.generativeai as genai

app = Flask(__name__, template_folder="../templates", static_folder="../static")

genai.configure(api_key="YOUR_GEMINI_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_recipe():
    data = request.get_json()
    ingredients = data.get('ingredients', '')
    preferences = data.get('preferences', '')
    time = data.get('time', '')
    cuisine = data.get('cuisine', '')

    prompt = f"""
    You are a professional chef assistant.
    Suggest 3 creative recipes using these ingredients: {ingredients}.
    Preferences: {preferences}. Cuisine: {cuisine}. Max cooking time: {time} minutes.

    For each recipe, provide:
    1. Recipe Title
    2. Estimated Time
    3. Ingredients List
    4. Steps
    5. Missing Ingredients
    6. Short Note or Tip
    """

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    return jsonify({"response": response.text})

# Adapter for serverless environments
handler = Mangum(app)
