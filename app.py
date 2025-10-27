from flask import Flask, render_template, request, jsonify
from mangum import Mangum
import google.generativeai as genai
from googleapiclient.discovery import build
import re
import os

app = Flask(__name__, template_folder="templates", static_folder="static")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# YouTube API setup
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Image generation removed as per user request

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_recipe():
    try:
        data = request.get_json()
        ingredients = data.get('ingredients', '')
        preferences = data.get('preferences', '')
        time = data.get('time', '')
        cuisine = data.get('cuisine', '')

        if not ingredients.strip():
            return jsonify({"error": "Please provide some ingredients."}), 400

        prompt = f"""
        You are a professional chef assistant.
        Suggest 3 creative recipes using these ingredients: {ingredients}.
        Preferences: {preferences}. Cuisine: {cuisine}. Max cooking time: {time} minutes.

        For each recipe, provide in plain text with emojis for better appearance, without any markdown formatting like **:
        1. 🍽️ Recipe Title (one should be exact title that i provided for example egg noodles should give egg noodles only do't use chicken like that)
        2. ⏱️ Estimated Time
        3. 🛒 Ingredients List
        4. 👨‍🍳 Steps
        5. 🛍️ Missing Ingredients
        6. 💡 Short Note or Tip
        """

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        # Parse the response to extract recipe titles
        recipes_text = response.text
        recipe_titles = re.findall(r'🍽️ (.*?)\n', recipes_text)

        # For each recipe, get YouTube link and thumbnail
        enhanced_recipes = []
        for i, title in enumerate(recipe_titles[:3]):  # Limit to 3 recipes
            youtube_link, thumbnail_url = search_youtube_video(title)
            # Insert YouTube link and thumbnail into the recipe text
            recipe_block = recipes_text.split('\n\n')[i]  # Assuming recipes are separated by double newlines
            enhanced_recipe = recipe_block + f"\n7. 📺 YouTube Video Link: {youtube_link}\n8. 🖼️ YouTube Thumbnail: {thumbnail_url}"
            enhanced_recipes.append(enhanced_recipe)

        enhanced_response = '\n\n'.join(enhanced_recipes)

        return jsonify({"response": enhanced_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
# Adapter for serverless environments
handler = Mangum(app)

def search_youtube_video(query):
    try:
        request = youtube.search().list(
            part="snippet",
            q=query + " recipe cooking tutorial",
            type="video",
            order="relevance",
            maxResults=1
        )
        response = request.execute()
        if response['items']:
            video_id = response['items'][0]['id']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            return video_url, thumbnail_url
        return "No video found", ""
    except Exception as e:
        return f"Error fetching video: {str(e)}", ""
            

if __name__ == '__main__':
    app.run(debug=True)
