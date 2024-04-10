from flask import Flask, request, jsonify
from openai import OpenAI
import os
from dotenv import dotenv_values
from ollama import Client
import json
import ollama
from collections import Counter
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build

config = dotenv_values(".env")

client = OpenAI(api_key=config['OPENAI_API_KEY'])

app = Flask(__name__)


## example curl to test: 
#curl -X POST http://127.0.0.1:80/summarize-entry \  
#-H "Content-Type: application/json" \
#-d '{"journal_entry": "today was a really weird day, but I hardly slept. I was pretty sad because of it. my dog is doing better today. I had my favorite cereal and it really motivated me. Specifically frosted flakes."}'

@app.route('/summarize-entry', methods=['POST'])
def summarize_entry():
    data = request.json
    journal_entry = data.get('journal_entry')

    if not journal_entry:
        return jsonify({'error': 'No journal entry provided'}), 400

    try:
        # Adjusted to the new interface
        response = client.chat.completions.create(model="gpt-3.5-turbo",  # this can change, but let's keep it to this to start with
        messages=[{
            "role": "system",
            "content": "Summarize the following journal entry. Write the summary as if you're telling the person what they did or felt that day. Start by saying /'On this day/'." # the instruction given to the model
        }, {
            "role": "user",
            "content": journal_entry # the journal entry
        }])
        summary = response.choices[0].message.content # the summary of the journal entry

        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/create_title', methods=['POST'])
def create_title():
    data = request.json
    journal_entry = data.get('journal_entry')
    if not journal_entry:
        return jsonify({'error': 'No journal entry provided'}), 400
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Create a title for the following content:"
                },
                {
                    "role": "user",
                    "content": journal_entry
                }
            ]
        )
        title = response.choices[0].message.content
        return jsonify({'title': title})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
## in order to test this out, you can run the following cURL command in your terminal:
#curl -X POST http://127.0.0.1:80/create_title \
#-H "Content-Type: application/json" \
#-d '{"journal_entry": "today was a really weird day, but I hardly slept. I was pretty sad because of it. my dog is doing better today. I had my favorite cereal and it really motivated me. Specifically frosted flakes."}'

@app.route('/ollama_summarize_entry', methods=['POST'])
def ask_ollama():
    data = request.json
    question = "With less than 100 words, please summarize this journal entry as if it will go in a record (write it in a serious way but with conversational words, do not say \"Here's a summary...\", write it in second-person, and don't say today, instead say on this day): " + data.get('journal_entry')
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    try:
        client = Client(host='http://backend.auto-mate.cc:11434')
        response = client.generate(model='llama2:13b', prompt=question, stream=False)
        answer = response['response'] 
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/title_generation', methods=['POST'])
def title_generation():
    data = request.json
    journal_entry = data.get('journal_entry')

    if not journal_entry:
        return jsonify({'error': 'No journal entry provided'}), 400

    try:
        # Adjusted to the new interface
        response = client.chat.completions.create(model="gpt-3.5-turbo",  # this can change, but let's keep it to this to start with
        messages=[{
            "role": "system",
            "content": "You are acting as a title generator for a journaling app. Every message sent to you will be a journal entry and you will respond with a short title that fits the entry. Do not put the title in quotes or respond with anything else but the complete title." # the instruction given to the model
        }, {
            "role": "user",
            "content": journal_entry # the journal entry
        }])
        summary = response.choices[0].message.content # the AI generated title of the journal entry

        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/search_meditation_video', methods=['POST'])
def search_meditation_video():
    data = request.json
    entries = data.get('entries')
    if not entries:
        return jsonify({'error': 'No entries provided'}), 400

    # # of words in the entries
    word_counts = Counter()
    for entry in entries:
        words = entry.split()
        word_counts.update(words)

    # Top 5 most frequent words
    most_frequent_words = [word for word, _ in word_counts.most_common(5)]

    # make search query
    search_query = "meditation " + " ".join(most_frequent_words)

    # init YouTube API client
    youtube = build('youtube', 'v3', developerKey=config['GOOGLE_API_KEY'])

    # search for videos on YouTube
    search_response = youtube.search().list(
        q=search_query,
        part='id,snippet',
        maxResults=1,
        type='video'
    ).execute()

    # pull link to the first video URL
    if search_response['items']:
        video_id = search_response['items'][0]['id']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        return jsonify({'video_url': video_url})
    else:
        return jsonify({'error': 'No videos found'}), 404
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
