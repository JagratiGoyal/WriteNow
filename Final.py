import requests
import gradio as gr
import random
import tempfile
from serpapi import GoogleSearch

# ================= OPENROUTER CONFIG =================
API_KEY = "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"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "openai/gpt-4o-mini"

# ================= LOAD TRENDS =================
params = {
  "engine": "google_trends_trending_now",  
  "geo": "IN",  
  "api_key": "9bbace14ceaefb9a1b6ca8ee02229d775d04c29e4445b7078653288c7a18bd2c"
}

search = GoogleSearch(params)
results = search.get_dict()
trends_data = results["trending_searches"]

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
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            return f"Error from API: {response.status_code} {response.text}"
    except Exception as e:
        return f"Error calling API: {e}"

# ================= TOP 5 TREND SUGGESTION =================
def suggest_top_trends(brand, product, platform):
    if not brand or not platform:
        return "", []

    product_text = f" (Product: {product})" if product else ""
    trends_text = "\n".join(trends_list)

    prompt = f"""
You are a marketing strategist. Given these trends:
{trends_text}

For the brand {brand}{product_text} on platform {platform}, select the top 5 trends most relevant.
Return each trend in ONE line using this format:

Rank Trend Name — Relevance to Brand (include suggested emojis & hashtags)

Keep each line short and crisp (under 40 words). Rank 1 is most relevant.
"""
    output = call_openrouter(prompt)
    lines = [line.strip() for line in output.splitlines() if line.strip()]

    top_trends = []
    for line in lines:
        if line[0].isdigit() and (line[1] == "." or line[1] == ")"):
            trend_name = line.split(" ", 1)[-1].split("—")[0].strip()
            top_trends.append(trend_name)
        if len(top_trends) >= 5:
            break

    if not top_trends:
        top_trends = random.sample(trends_list, min(5, len(trends_list)))

    return output, top_trends

# ================= TEXT POST GENERATION =================
def generate_text_posts(rank_number, top_trends, brand, platform, tone, product):
    if not top_trends or not rank_number:
        return ["Please select a trend rank first."] * 3

    selected_trend = top_trends[int(rank_number)-1]
    product_text = f" for its product {product}" if product else ""
    posts = []
    for i in range(3):
        prompt = f"""
You are the brand manager for {brand}{product_text}.
Write a crisp, text-only {platform} post about "{selected_trend}" in a {tone} tone.
Make it directly relatable to {brand}{product_text}, integrating the trend naturally.
Keep it under 80 words, emotionally engaging, include relevant hashtags and emojis.
No extra commentary — just the post.
"""
        post = call_openrouter(prompt)
        posts.append(post)
    return posts

# ================= DOWNLOAD FUNCTION =================
def download_single_post(text):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
    tmp.write(text)
    tmp.close()
    return tmp.name

# ================= GRADIO UI =================
with gr.Blocks(css="""
    body {background-color: #FAF9F6; font-family: 'Inter', sans-serif;}
    .header {
        background: linear-gradient(90deg, #6B5B95, #9C7CBF);
        color: #FAF9F6;
        padding: 12px;
        border-radius: 12px;
        font-size: 28px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 12px;
    }
    .label {font-weight: bold; color: #333333; margin-bottom: 5px;}
    .input-box {background-color: #F5F0E6; border-radius: 8px; padding: 5px; font-weight: normal;}
    .trend-box {background-color: #E0E7FF; padding: 8px; border-radius: 8px; font-size: 14px; margin-bottom:5px; resize: none;}
    .post-card {
        background: #FFF9F2;
        padding: 10px 12px;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        margin-bottom: 8px;
        font-size: 14px;
        transition: all 0.2s ease;
    }
    .suggest-btn {background-color: #6B5B95; color: #FAF9F6; border-radius: 8px; padding: 6px 14px; font-weight:bold; transition: all 0.2s ease;}
    .suggest-btn:hover {background-color: #9C7CBF; transform: scale(1.05);}
    .download-btn {background-color: #FAF9F6; color: #6B5B95; border-radius: 6px; padding: 4px 10px; font-weight:bold; margin-right:5px; transition: all 0.2s ease;}
    .download-btn:hover {background-color: #F0E8FF; transform: scale(1.05);}
""") as demo:

    gr.HTML("<div class='header'>WriteNow - Your Post, Right on Time</div>")

    # Inputs
    with gr.Row():
        brand_name = gr.Textbox(label="Brand Name", placeholder="e.g., Nestlé", elem_classes="label input-box")
        product_name = gr.Textbox(label="Brand Product (Optional)", placeholder="e.g., Maggi Noodles", elem_classes="label input-box")
    with gr.Row():
        platform_choice = gr.Dropdown(
            label="Platform",
            choices=["Instagram", "Facebook", "Twitter"],
            value="Instagram",
            elem_classes="label input-box"
        )
        tone_choice = gr.Dropdown(
            label="Tone / Style",
            choices=["Friendly", "Conversational", "Fun", "Enthusiastic", "Energetic", "Aspirational", "Informative", "Witty"],
            value="Friendly",
            elem_classes="label input-box"
        )

    # Top 5 Trends
    suggest_btn = gr.Button("📈 Suggest Top 5 Trends", elem_classes="suggest-btn")
    ranked_trends_output = gr.Textbox(label="📄 Top 5 Trends", interactive=False, elem_classes="trend-box", lines=1)
    rank_number = gr.Dropdown(label="Select Trend by Rank", choices=["1", "2", "3", "4", "5"], value="1", elem_classes="input-box")

    # Posts stacked vertically
    post1_output = gr.Textbox(label="Post 1", lines=3, interactive=False, elem_classes="post-card")
    post2_output = gr.Textbox(label="Post 2", lines=3, interactive=False, elem_classes="post-card")
    post3_output = gr.Textbox(label="Post 3", lines=3, interactive=False, elem_classes="post-card")

    # Download buttons at bottom
    download1_btn = gr.Button("📄 Download Post 1", elem_classes="download-btn")
    download1_file = gr.File()
    download2_btn = gr.Button("📄 Download Post 2", elem_classes="download-btn")
    download2_file = gr.File()
    download3_btn = gr.Button("📄 Download Post 3", elem_classes="download-btn")
    download3_file = gr.File()

    # State to store top trends
    top_trends_state = gr.State()

    # ================= CALLBACKS =================
    suggest_btn.click(
        fn=suggest_top_trends,
        inputs=[brand_name, product_name, platform_choice],
        outputs=[ranked_trends_output, top_trends_state]
    )

    rank_number.change(
        fn=generate_text_posts,
        inputs=[rank_number, top_trends_state, brand_name, platform_choice, tone_choice, product_name],
        outputs=[post1_output, post2_output, post3_output]
    )

    download1_btn.click(download_single_post, inputs=post1_output, outputs=download1_file)
    download2_btn.click(download_single_post, inputs=post2_output, outputs=download2_file)
    download3_btn.click(download_single_post, inputs=post3_output, outputs=download3_file)

demo.launch(share=True)
