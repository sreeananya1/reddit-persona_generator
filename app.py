from flask import Flask, render_template, request
import requests
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# -----------------------------
# REDDIT FETCH (NO API KEY)
# -----------------------------
def fetch_user_content(username, limit=20):

    headers = {"User-Agent": "Mozilla/5.0"}
    texts = []

    try:
        c_url = f"https://www.reddit.com/user/{username}/comments.json?limit={limit}"
        c_res = requests.get(c_url, headers=headers)

        if c_res.status_code == 200:
            try:
                data = c_res.json()
                for item in data.get("data", {}).get("children", []):
                    body = item["data"].get("body", "")
                    if body:
                        texts.append(body)
            except:
                pass

        p_url = f"https://www.reddit.com/user/{username}/submitted.json?limit={limit}"
        p_res = requests.get(p_url, headers=headers)

        if p_res.status_code == 200:
            try:
                data = p_res.json()
                for item in data.get("data", {}).get("children", []):
                    title = item["data"].get("title", "")
                    selftext = item["data"].get("selftext", "")
                    texts.append(title + " " + selftext)
            except:
                pass

        if not texts:
            return ["No data found"], None

        return texts, None

    except Exception as e:
        return None, str(e)


# -----------------------------
# AI PERSONA ENGINE (FIXED)
# -----------------------------
def detect_topic(text):
    text = text.lower()

    if any(word in text for word in ["movie", "film", "hollywood", "actor", "cinema"]):
        return "entertainment"

    elif any(word in text for word in ["stock", "money", "finance", "investment", "crypto"]):
        return "finance"

    elif any(word in text for word in ["code", "python", "developer", "ai", "data"]):
        return "tech"

    elif any(word in text for word in ["sport", "cricket", "football", "game"]):
        return "sports"

    else:
        return "general"
    

    
def generate_persona(content):
    text = " ".join(content)

    topic = detect_topic(text)

    personas = {
        "entertainment": {
            "interests": "Movies, Celebrity Culture, Cinema",
            "personality": "Expressive, creative, emotionally driven",
            "writing_style": "Casual and expressive",
            "summary": "A pop-culture enthusiast who enjoys films and entertainment content."
        },

        "finance": {
            "interests": "Investing, Stocks, Crypto, Financial Growth",
            "personality": "Analytical, risk-aware, strategic",
            "writing_style": "Logical and data-driven",
            "summary": "A finance-focused thinker interested in wealth building and investments."
        },

        "tech": {
            "interests": "Programming, AI, Data Science, Software Development",
            "personality": "Logical, curious, problem-solver",
            "writing_style": "Technical and structured",
            "summary": "A tech enthusiast passionate about coding and AI systems."
        },

        "sports": {
            "interests": "Sports, Fitness, Competition",
            "personality": "Energetic, competitive, disciplined",
            "writing_style": "Direct and enthusiastic",
            "summary": "A sports-oriented personality driven by competition and activity."
        },

        "general": {
            "interests": "General knowledge, browsing, mixed interests",
            "personality": "Balanced, curious, open-minded",
            "writing_style": "Simple and neutral",
            "summary": "A general user with mixed interests across domains."
        }
    }

    base = personas[topic]

    # add small variation so it doesn't feel identical
    base["writing_style"] += random.choice([
        " with slight personal tone.",
        " with structured clarity.",
        " with expressive explanation style."
    ])

    return base


# -----------------------------
# FLASK ROUTE
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    try:
        if request.method == "POST":

            username = request.form["username"]

            content, error = fetch_user_content(username)

            persona = generate_persona(content)

            return render_template(
                "result.html",
                username=username,
                persona=persona
            )

        return render_template("index.html")

    except Exception as e:
        return f"ERROR OCCURRED: {str(e)}"


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)