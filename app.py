from flask import Flask, render_template, request
import requests
from groq import Groq
import os
from dotenv import load_dotenv

# -----------------------------
# LOAD ENV
# -----------------------------
load_dotenv()

# -----------------------------
# GROQ API
# -----------------------------
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

app = Flask(__name__)


# -----------------------------
# REDDIT FETCH
# -----------------------------
def fetch_user_content(username, limit=20):

    headers = {
        "User-Agent": "RedditPersonaBot/1.0"
    }

    texts = []

    try:

        # COMMENTS
        comments_url = (
            f"https://www.reddit.com/user/"
            f"{username}/comments/.json?limit={limit}"
        )

        c_res = requests.get(
            comments_url,
            headers=headers,
            timeout=10
        )

        

        if c_res.status_code == 200:

            data = c_res.json()

            for item in data.get(
                "data", {}
            ).get("children", []):

                body = item["data"].get(
                    "body", ""
                )

                if body:
                    texts.append(body)

        # POSTS
        posts_url = (
            f"https://www.reddit.com/user/"
            f"{username}/submitted/.json?limit={limit}"
        )

        p_res = requests.get(
            posts_url,
            headers=headers,
            timeout=10
        )

        

        if p_res.status_code == 200:

            data = p_res.json()

            for item in data.get(
                "data", {}
            ).get("children", []):

                title = item["data"].get(
                    "title", ""
                )

                selftext = item["data"].get(
                    "selftext", ""
                )

                combined = (
                    f"{title} {selftext}"
                ).strip()

                if combined:
                    texts.append(combined)


        if not texts:
            return [
                "User has limited or private Reddit activity."
            ], None

        return texts, None

    except Exception as e:
        
        return None, str(e)


# -----------------------------
# AI PERSONA ENGINE
# -----------------------------

def generate_persona(content):

    text_data = "\n".join(content[:40])

    prompt = f"""
    Analyze this Reddit user's activity.

    Reddit content:
    {text_data}

    Return ONLY this exact format:

    Interests: <short answer>

    Personality: <short answer>

    Writing Style: <short answer>

    Summary: <2-3 sentence realistic summary>

    Keep answers short and evidence-based.
    """

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5
        )

        result = response.choices[0].message.content


        persona = {
            "interests": "",
            "personality": "",
            "writing_style": "",
            "summary": ""
        }

        lines = result.split("\n")

        for line in lines:

            clean = (
                line.replace("*", "")
                .strip()
            )

            if clean.lower().startswith("interests:"):
                persona["interests"] = (
                    clean.split(":", 1)[1]
                    .strip()
                )

            elif clean.lower().startswith("personality:"):
                persona["personality"] = (
                    clean.split(":", 1)[1]
                    .strip()
                )

            elif clean.lower().startswith("writing style:"):
                persona["writing_style"] = (
                    clean.split(":", 1)[1]
                    .strip()
                )

            elif clean.lower().startswith("summary:"):
                persona["summary"] = (
                    clean.split(":", 1)[1]
                    .strip()
                )

        # fallback values
        if not persona["interests"]:
            persona["interests"] = "Not enough data"

        if not persona["personality"]:
            persona["personality"] = "Not enough data"

        if not persona["writing_style"]:
            persona["writing_style"] = "Not enough data"

        if not persona["summary"]:
            persona["summary"] = result

        return persona

    except Exception as e:

        return {
            "interests": "Unavailable",
            "personality": "Unavailable",
            "writing_style": "Unavailable",
            "summary": f"Error: {str(e)}"
        }

# -----------------------------
# HOME ROUTE
# -----------------------------
@app.route(
    "/",
    methods=["GET", "POST"]
)
def home():

    if request.method == "POST":

        username = request.form[
            "username"
        ]

        content, error = (
            fetch_user_content(
                username
            )
        )

        if error:
            return (
                f"Error: {error}"
            )

        persona = (
            generate_persona(
                content
            )
        )

        return render_template(
            "result.html",
            username=username,
            persona=persona
        )

    return render_template(
        "index.html"
    )


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
