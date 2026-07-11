from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import uuid
import shutil
import zipfile

app = Flask(__name__)
DOWNLOAD_PATH = '/tmp/downloads'
COOKIES_PATH = '/app/cookies.txt'

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)


def download_mp3(url, session_dir):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }],
        'outtmpl': os.path.join(session_dir, '%(title)s.%(ext)s'),
        'noplaylist': True,
    }

    if os.path.exists(COOKIES_PATH):
        ydl_opts['cookiefile'] = COOKIES_PATH

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info.get('title', 'audio')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    urls = request.json.get('urls', [])
    urls = [u.strip() for u in urls if u.strip()]

    if not urls:
        return jsonify({"error": "URL을 하나 이상 입력해 주세요."}), 400

    session_id = uuid.uuid4().hex[:8]
    session_dir = os.path.join(DOWNLOAD_PATH, session_id)
    os.makedirs(session_dir, exist_ok=True)

    results = []
    for url in urls:
        try:
            title = download_mp3(url, session_dir)
            results.append({"url": url, "status": "success", "title": title})
        except Exception as e:
            results.append({"url": url, "status": "error", "message": str(e)})

    mp3_files = [f for f in os.listdir(session_dir) if f.endswith('.mp3')]

    if not mp3_files:
        shutil.rmtree(session_dir, ignore_errors=True)
        return jsonify({"error": "변환에 성공한 파일이 없습니다.", "results": results}), 500

    zip_path = os.path.join(DOWNLOAD_PATH, f'{session_id}.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in mp3_files:
            zf.write(os.path.join(session_dir, f), arcname=f)

    shutil.rmtree(session_dir, ignore_errors=True)

    response = send_file(zip_path, as_attachment=True, download_name='converted_mp3.zip')

    @response.call_on_close
    def cleanup():
        if os.path.exists(zip_path):
            os.remove(zip_path)

    return response


if __name__ == '__main__':
    app.run(debug=True)
