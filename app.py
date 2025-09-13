from flask import Flask, render_template, request, jsonify
from faster_whisper import WhisperModel

app = Flask(__name__)
app.config["SECRET_KEY"] = "oauh"

model = WhisperModel("tiny")

@app.route("/")
def home():
    return render_template("speech_to_text.html")

@app.route("/speech_to_text", methods=["POST"])
def speech_to_text():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    audio_file = request.files["file"]
    audio_path = f"/tmp/{audio_file.filename}"
    audio_file.save(audio_path)

    segments, info = model.transcribe(audio_path)
    transcript = " ".join([seg.text for seg in segments])

    return jsonify({"transcript": transcript})

if __name__ == '__main__':
    app.run(debug=True)
