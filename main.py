import nltk
from nltk.corpus import stopwords
import pymorphy2
from sklearn.feature_extraction.text import TfidfVectorizer
import json
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, abort, redirect, request, jsonify, send_file
import requests
from tempfile import NamedTemporaryFile
import ffmpeg


RH_VOICE_ENDPOINT = "http://localhost:8080"
TRANSCRIBITION_ENDPOINT = "http://localhost:8002"

db = json.load(open("db.json"))
nltk.download("stopwords")
nltk.download("punkt")
russian_stopwords = stopwords.words("russian")
morph = pymorphy2.MorphAnalyzer()

transcribing = False


def preprocess(text):
    tokens = nltk.word_tokenize(text.lower())
    tokens = [morph.parse(word)[0].normal_form for word in tokens if word.isalnum()]
    tokens = [token for token in tokens if token not in russian_stopwords]
    return tokens


vectorizer = TfidfVectorizer(tokenizer=preprocess)
tfidf_matrix = vectorizer.fit_transform([q["question"] for q in db])


def ask_question(query):
    query_vec = vectorizer.transform([query])
    similarity = cosine_similarity(query_vec, tfidf_matrix)
    max_index = similarity.argmax()
    return db[max_index]["answer"]


app = Flask(__name__)


@app.route("/qa_text", methods=["POST"])
def qa():
    global transcribing
    if transcribing:
        return abort(500, "Transcribition in process")
    transcribing = True

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Forward file to another endpoint
    response = requests.post(
        f"{TRANSCRIBITION_ENDPOINT}/transcribe",
        files={"file": (file.filename, file.stream, file.content_type)},
    )
    transcribing = False

    response = response.json()
    question = response["transcription"]
    print("Question", question)
    answer = ask_question(question)
    print("Answer", answer)
    return {"question": question, "answer": answer}


@app.route("/qa_voice", methods=["POST"])
def qa_voice():
    global transcribing
    if transcribing:
        return abort(500, "Transcribition in process")
    transcribing = True

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Forward file to another endpoint
    response = requests.post(
        f"{TRANSCRIBITION_ENDPOINT}/transcribe",
        files={"file": (file.filename, file.stream, file.content_type)},
    )
    transcribing = False

    response = response.json()
    question = response["transcription"]
    print("Question", question)
    answer = ask_question(question)
    print("Answer", answer)
    voice_url = f"{RH_VOICE_ENDPOINT}/say?text={answer.replace(' ', '%20')}&voice=yuriy&format=wav"
    voice_response = requests.get(voice_url)
    if voice_response.status_code != 200:
        return jsonify({"error": "Failed to generate voice response"}), 500

    temp = NamedTemporaryFile(delete=False, suffix=".wav")
    temp.write(voice_response.content)
    temp.close()
    (ffmpeg.input(temp.name).output(temp.name, ar="8000").run())

    return send_file(temp.name, as_attachment=True, download_name="response.mp3")


if __name__ == "__main__":
    app.run(debug=True, port=4011, host="0.0.0.0")
