from flask import Flask, render_template, request, jsonify
from faster_whisper import WhisperModel

app = Flask(__name__)
app.config["SECRET_KEY"] = "oauh"

model = WhisperModel("tiny")

@app.route("/")
def home():
    return render_template("text_to_text.html")

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

@app.route('/submit_reflection', methods=['POST'])
def submit_reflection():
    submitted = False
    work_done = request.form.get('work', '')
    hours_worked = request.form.get('hours', '0')
    help_self = request.form.get('help', '')
    future_impact = request.form.get('impact', '')

    submitted = True

    return render_template(
        'text_to_text.html',
        submitted=submitted,
        work_done=work_done,
        hours_worked=hours_worked,
        help_self=help_self,
        future_impact=future_impact
    )

if __name__ == '__main__':
    app.run(debug=True)
