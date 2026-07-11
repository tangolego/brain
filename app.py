from flask import Flask, render_template, request, jsonify
import yt_dlp
import os

app = Flask(__name__)
DOWNLOAD_PATH = './downloads'

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

def download_mp3(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s.%(ext)s'),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    urls = request.json.get('urls', [])
    results = []
    for url in urls:
        try:
            download_mp3(url)
            results.append({"url": url, "status": "success"})
        except Exception as e:
            results.append({"url": url, "status": "error", "message": str(e)})
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)