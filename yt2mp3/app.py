from flask import Flask, render_template, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# 검색 기능: 썸네일 주소까지 안전하게 가져옵니다
@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')
    ydl_opts = {'quiet': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(f"ytsearch5:{query}", download=False)
            videos = []
            for v in result.get('entries', []):
                # URL 추출
                url = v.get('webpage_url') or v.get('url')
                if not url and 'id' in v:
                    url = f"https://www.youtube.com/watch?v={v['id']}"

                # 썸네일 추출 (리스트 형태일 경우 마지막 고화질 주소 추출)
                thumbnail = ''
                thumbnails = v.get('thumbnails', [])
                if thumbnails and isinstance(thumbnails, list):
                    thumbnail = thumbnails[-1].get('url')
                elif isinstance(v.get('thumbnail'), str):
                    thumbnail = v.get('thumbnail')
                
                if v.get('title') and url:
                    videos.append({'title': v['title'], 'url': url, 'thumbnail': thumbnail})
            return jsonify(videos)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# 다운로드 기능: 여러 개 URL 한 번에 처리
@app.route('/download', methods=['POST'])
def download():
    urls = request.json.get('urls', [])
    if not urls:
        return jsonify({"status": "error", "message": "입력된 URL이 없습니다."})

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'restrictfilenames': True,  # 파일 이름의 특수문자/슬래시 오류 방지
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(urls)
        return jsonify({"status": "success", "message": f"{len(urls)}개 변환 완료!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)