from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# 🔑 Configure your Gemini API key
genai.configure(api_key="AIzaSyAfx1btejKtGHduf0ObU8TOiwIsXS2MXHw")

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
    2. Estimated Time (in minutes)
    3. Ingredients List
    4. Step-by-Step Cooking Instructions
    5. Missing Ingredients (if any)
    6. Short Note or Tip
    """

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    return jsonify({"response": response.text})

if __name__ == '__main__':
    app.run(debug=True)
