import praw
import openai
import re
import os
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, OPENAI_API_KEY

# Set up OpenAI
openai.api_key = OPENAI_API_KEY

# Set up Reddit API
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

def extract_username(url):
    """Extracts username from Reddit profile URL"""
    match = re.search(r'reddit\.com/user/([^/]+)/?', url)
    return match.group(1) if match else None

def fetch_user_data(username, limit=50):
    """Fetches posts and comments from a Reddit user"""
    redditor = reddit.redditor(username)
    posts = []
    comments = []

    try:
        for post in redditor.submissions.new(limit=limit):
            posts.append({
                "title": post.title,
                "body": post.selftext,
                "url": f"https://www.reddit.com{post.permalink}"
            })
        for comment in redditor.comments.new(limit=limit):
            comments.append({
                "body": comment.body,
                "url": f"https://www.reddit.com{comment.permalink}"
            })
    except Exception as e:
        print(f"[!] Error fetching data: {e}")

    return posts, comments

def generate_prompt(posts, comments):
    """Formats posts/comments for GPT analysis"""
    examples = ""
    for p in posts[:10]:
        examples += f"\n[POST] {p['title']}\n{p['body']}\nURL: {p['url']}\n"
    for c in comments[:10]:
        examples += f"\n[COMMENT] {c['body']}\nURL: {c['url']}\n"
    
    return f"""
You are an AI language model that generates user personas based on Reddit activity.

From the posts and comments below, extract the user's persona characteristics, such as:
- Name (if any)
- Age Range
- Occupation (if guessable)
- Interests
- Values / Beliefs
- Tone of communication
- Political/Social views (if any)
- Subreddits they are active in
- Any unique personality traits

For each trait, provide a short quote from the post or comment with the URL.

Here is their Reddit activity:
{examples}
"""

def generate_persona(prompt):
    """Calls OpenAI to generate the user persona"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",

        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def save_to_file(username, persona_text):
    """Saves the persona to a .txt file"""
    os.makedirs("outputs", exist_ok=True)
    filename = f"outputs/{username}_persona.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(persona_text)
    print(f"✅ Persona saved to {filename}")

def main():
    url = input("🔗 Enter Reddit profile URL (e.g., https://www.reddit.com/user/kojied/): ").strip()
    username = extract_username(url)
    if not username:
        print("❌ Invalid Reddit URL.")
        return

    print(f"🔍 Fetching data for user: {username}...")
    posts, comments = fetch_user_data(username)
    print(f"✅ Fetched {len(posts)} posts and {len(comments)} comments.")

    print("🤖 Generating user persona...")
    prompt = generate_prompt(posts, comments)
    persona = generate_persona(prompt)

    save_to_file(username, persona)

if __name__ == "__main__":
    main()
