import os
import re
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from googleapiclient.discovery import build

# ------------------------------------------------------------
# Flask app configuration
# ------------------------------------------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")

# ------------------------------------------------------------
# Configure API keys (use environment variables in production)
# ------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_LOCAL_GEMINI_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "YOUR_LOCAL_YOUTUBE_KEY")

genai.configure(api_key=GEMINI_API_KEY)
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@app.route("/")
def index():
    """Serve the main web page."""
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate_recipe():
    """Generate recipes using Gemini + YouTube data."""
    try:
        data = request.get_json()
        ingredients = data.get("ingredients", "")
        preferences = data.get("preferences", "")
        time = data.get("time", "")
        cuisine = data.get("cuisine", "")

        if not ingredients.strip():
            return jsonify({"error": "Please provide some ingredients."}), 400

        prompt = f"""
        You are a professional chef assistant.
        Suggest 3 creative recipes using these ingredients: {ingredients}.
        Preferences: {preferences}. Cuisine: {cuisine}. Max cooking time: {time} minutes.

        For each recipe, provide:
        1. 🍽️ Recipe Title (use exact names like 'egg noodles' if given)
        2. ⏱️ Estimated Time
        3. 🛒 Ingredients List
        4. 👨‍🍳 Steps
        5. 🛍️ Missing Ingredients
        6. 💡 Short Note or Tip
        """

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        recipes_text = response.text or ""

        recipe_titles = re.findall(r"🍽️ (.*?)\n", recipes_text)
        enhanced_recipes = []

        for i, title in enumerate(recipe_titles[:3]):  # Only top 3
            youtube_link, thumbnail_url = search_youtube_video(title)
            recipe_block = recipes_text.split("\n\n")[i]
            enhanced_recipe = (
                recipe_block
                + f"\n7. 📺 YouTube Video Link: {youtube_link}"
                + f"\n8. 🖼️ YouTube Thumbnail: {thumbnail_url}"
            )
            enhanced_recipes.append(enhanced_recipe)

        return jsonify({"response": "\n\n".join(enhanced_recipes)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------------
# Helper function: search YouTube for a recipe video
# ------------------------------------------------------------
def search_youtube_video(query):
    try:
        request = youtube.search().list(
            part="snippet",
            q=query + " recipe cooking tutorial",
            type="video",
            order="relevance",
            maxResults=1,
        )
        response = request.execute()
        if response.get("items"):
            video_id = response["items"][0]["id"]["videoId"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            return video_url, thumbnail_url
        return "No video found", ""
    except Exception as e:
        return f"Error fetching video: {str(e)}", ""


# ------------------------------------------------------------
# Run locally
# ------------------------------------------------------------
if __name__ == "__main__":
    # On Vercel, the runtime will import `app` directly.
    app.run(host="0.0.0.0", port=5000, debug=True)
