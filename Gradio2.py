import json
import requests
import gradio as gr
import random
from serpapi import GoogleSearch
import json

# ================= OPENROUTER CONFIG =================
API_KEY = "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"  # <-- paste your OpenRouter API key here
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "openai/gpt-4o-mini"

# ================= LOAD TRENDS =================
# TODO: When finalising uncomment the paras below
# params = {
#   "engine": "google_trends_trending_now",  
#   "geo": "IN",  
#   "api_key": "9bbace14ceaefb9a1b6ca8ee02229d775d04c29e4445b7078653288c7a18bd2c"
# }

# search = GoogleSearch(params)
# results = search.get_dict()
# trends_data = results["trending_searches"]

# TODO: When finalising, remove the 2 lines below
with open("my_list.json", encoding="utf-8") as f:
    trends_data = json.load(f)

trends_list = [trend["query"] for trend in trends_data if trend.get("search_volume", 0) >= 10000]

# ================= OPENROUTER CALL =================
def call_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a skilled marketing strategist and copywriter."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            return f"Error from API: {response.status_code} {response.text}"
    except Exception as e:
        return f"Error calling API: {e}"

# ================= TOP 5 TREND SUGGESTION =================
def suggest_top_trends(brand, platform):
    if not brand or not platform:
        return "", []

    trends_text = "\n".join(trends_list)
    prompt = f"""
    You are a marketing strategist. Given these trends:
    {trends_text}

    For the brand {brand} and platform {platform}, select the top 5 trends that are most relevant and aligned to the brand.
    Return the trends in ranked order, 1 being most relevant. Provide only the list, no extra text.
    """
    output = call_openrouter(prompt)
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    top_trends = []
    for line in lines:
        # Remove numbering if present
        if line[0].isdigit() and (line[1] == '.' or line[1] == ')'):
            top_trends.append(line[2:].strip())
        else:
            top_trends.append(line)
        if len(top_trends) >= 5:
            break
    if not top_trends:
        top_trends = random.sample(trends_list, 5)

    # Prepare ranked display
    ranked_text = "\n".join([f"{i+1}. {trend}" for i, trend in enumerate(top_trends)])
    return ranked_text, top_trends

# ================= TEXT POST GENERATION =================
def generate_text_posts(rank_number, top_trends, brand, platform, tone):
    if not top_trends or not rank_number:
        return "Please select a trend rank first."

    selected_trend = top_trends[int(rank_number)-1]
    posts = []
    for i in range(3):
        prompt = f"""
You are the brand manager for {brand}.
Write a crisp, text-only {platform} post about "{selected_trend}" in a {tone} tone.
Make it directly relatable to {brand}, integrating the trend naturally.
Keep it under 80 words, emotionally engaging, include relevant hashtags and emojis.
No extra commentary — just the post.
"""
        post = call_openrouter(prompt)
        posts.append(post)
    return "\n\n---\n\n".join(posts)

# ================= DOWNLOAD FUNCTION =================
def download_posts(text):
    filename = "generated_posts.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    return filename

# ================= GRADIO UI =================
with gr.Blocks() as demo:
    gr.Markdown("## wRiteNow - Your Post, Right on Time")

    with gr.Row():
        brand_name = gr.Textbox(label="Brand Name", placeholder="e.g., Nestlé")
        platform_choice = gr.Dropdown(
            label="Platform",
            choices=["Instagram", "Facebook", "Twitter"],
            value="Instagram"
        )
        tone_choice = gr.Dropdown(
            label="Tone / Style",
            choices=[
                "Friendly", "Conversational", "Fun", "Enthusiastic",
                "Energetic", "Aspirational", "Informative", "Witty"
            ],
            value="Friendly"
        )

    # Step 1: Suggest top 5 ranked trends
    suggest_btn = gr.Button("Suggest Top 5 Trends")
    ranked_trends_output = gr.Textbox(label="Top 5 Trends (Ranked 1–5)", lines=7, interactive=False)
    rank_number = gr.Dropdown(label="Select Trend by Rank", choices=["1", "2", "3", "4", "5"], value="1")

    # Step 2: Generate posts for selected trend
    generate_btn = gr.Button("Generate 3 Post Variations")
    posts_output = gr.Textbox(label="Generated Posts", lines=12, interactive=True)
    download_btn = gr.File(label="Download Posts as TXT")

    # ================= STATE TO STORE TOP TRENDS =================
    top_trends_state = gr.State()

    # ================= CALLBACKS =================
    suggest_btn.click(
        fn=suggest_top_trends,
        inputs=[brand_name, platform_choice],
        outputs=[ranked_trends_output, top_trends_state]  # Save top_trends in state
    )

    generate_btn.click(
        fn=generate_text_posts,
        inputs=[rank_number, top_trends_state, brand_name, platform_choice, tone_choice],
        outputs=[posts_output]
    )

    download_btn.upload(
        fn=download_posts,
        inputs=[posts_output],
        outputs=[download_btn]
    )

demo.launch(share=True)
