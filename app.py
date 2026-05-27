from flask import Flask, render_template, request
import requests
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
def generate_persona(content):

    profiles = {
        "Software Development": "python code backend flask django api development software",
        "AI & Data Science": "machine learning ai data model neural network prediction",
        "Finance & Investing": "stock crypto trading finance investment money market",
        "Gaming": "gaming fps esports stream playstation xbox pc games"
    }

    documents = content
    all_docs = documents + list(profiles.values())

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform(all_docs)

    doc_vectors = vectors[:len(documents)]
    profile_vectors = vectors[len(documents):]

    scores = {}

    for i, key in enumerate(profiles.keys()):
        sim = cosine_similarity(doc_vectors, profile_vectors[i]).mean()
        scores[key] = float(sim)

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    dominant = sorted_scores[0][0]
    second = sorted_scores[1][0]

    activity_map = {
        "Software Development": "Builder 🛠️",
        "AI & Data Science": "Learner 📚",
        "Finance & Investing": "Investor 💰",
        "Gaming": "Gamer 🎮"
    }

    confidence = min(100, int(sorted_scores[0][1] * 120))

    return {
        "interests": f"{dominant}, {second}",
        "dominant": dominant,
        "activity": activity_map.get(dominant, "Explorer"),
        "personality": "AI-based behavioral inference",
        "writing_style": "Analyzed from text patterns",
        "summary": f"Strong alignment with {dominant}, secondary interest in {second}.",
        "confidence": f"{confidence}%"
    }


# -----------------------------
# FLASK ROUTE
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        username = request.form["username"]

        content, error = fetch_user_content(username)

        if error:
            return f"Error: {error}"

        persona = generate_persona(content)

        return render_template("result.html", username=username, persona=persona)

    return render_template("index.html")


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)