from flask import Flask, send_file, jsonify, render_template
import edge_tts
import asyncio
import os
import tempfile

app = Flask(__name__, template_folder='templates')

TEXT_FILE_PATH = 'result/book_page.txt'
TEXT_STORAGE = {
    "sentences": []
}

# 사용할 음성 이름 (변경 가능)
VOICE_NAME = "ko-KR-SunHiNeural"  # 여성 음성
# 다른 예: "ko-KR-InJoonNeural" (남성), "ko-KR-BongJinNeural"

def load_text_file():
    if not os.path.exists(TEXT_FILE_PATH):
        print(f"[ERROR] 파일이 존재하지 않습니다: {TEXT_FILE_PATH}")
        return

    with open(TEXT_FILE_PATH, encoding='utf-8') as f:
        text = f.read()
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        TEXT_STORAGE["sentences"] = sentences
        print(f"[INFO] 텍스트 파일 로드 완료 - 문장 {len(sentences)}개")

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/api/get-sentence-count', methods=['GET'])
def get_sentence_count():
    return jsonify({"count": len(TEXT_STORAGE["sentences"])})

@app.route('/api/get-audio/<int:sentence_id>', methods=['GET'])
def get_audio(sentence_id):
    sentences = TEXT_STORAGE["sentences"]
    if sentence_id < 0 or sentence_id >= len(sentences):
        return jsonify({"error": "Invalid sentence index"}), 404

    sentence = sentences[sentence_id]
    temp_path = os.path.join(tempfile.gettempdir(), f"tts_{sentence_id}.mp3")

    async def generate_tts():
        tts = edge_tts.Communicate(text=sentence, voice=VOICE_NAME)
        await tts.save(temp_path)

    asyncio.run(generate_tts())

    return send_file(temp_path, mimetype='audio/mpeg', as_attachment=False)

if __name__ == '__main__':
    load_text_file()
    app.run(debug=True)
