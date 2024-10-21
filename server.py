import os
import io
import json
import wave
import whisper
# import language_tool_python
from flask import Flask, request, jsonify, render_template
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer

app = Flask(__name__)

# Verzeichnis zum Speichern von Audiodateien
AUDIO_DIR = "audio_files"
os.makedirs(AUDIO_DIR, exist_ok=True)

MODEL_PATH = "models/vosk"

# Überprüfen, ob das Vosk-Modell vorhanden ist
def check_model():
    model_abs_path = os.path.abspath(MODEL_PATH)
    if not os.path.exists(model_abs_path):
        raise FileNotFoundError(f"Vosk model not found in {model_abs_path}. Please ensure the model is correctly placed.")
    else:
        print("Vosk model found:", model_abs_path)

check_model()

# Funktion zur Textkorrektur mit LanguageTool
def toolify(text):
    #tool = language_tool_python.LanguageTool('de-DE')
    return text #tool.correct(text)

# Initialisiere Vosk und Whisper
model_abs_path = os.path.abspath(MODEL_PATH)
model = Model(model_path=model_abs_path)
recognizer = KaldiRecognizer(model, 16000)

whisper_model = whisper.load_model("medium")  # Wähle je nach Ressourcen das richtige Modell (base, small, medium, large)

# Gemeinsame Funktion zur Audiokonvertierung
def convert_audio(audio_data):
    try:
        # Lade das Audio und konvertiere es in Mono, 16 kHz, 16-Bit PCM
        audio = AudioSegment.from_file(io.BytesIO(audio_data))
        original_channels = audio.channels
        original_frame_rate = audio.frame_rate
        original_sample_width = audio.sample_width

        # Konvertiere zu mono und setze die Samplerate auf 16000 Hz
        audio = audio.set_channels(1)  # Mono
        audio = audio.set_frame_rate(16000)  # 16 kHz
        audio = audio.set_sample_width(2)  # 16-Bit PCM

        # Speichere die konvertierte Audiodatei temporär
        wav_filename = os.path.join(AUDIO_DIR, "last_recording.wav")
        audio.export(wav_filename, format="wav")

        return wav_filename, {
            "original_channels": original_channels,
            "original_frame_rate": original_frame_rate,
            "original_sample_width": original_sample_width
        }
    except Exception as e:
        raise Exception(f"Audio conversion failed: {str(e)}")

####################################

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Setze maximale Dateigröße auf 16 MB

####################################

# Route für das Webinterface
@app.route('/')
def index():
    return render_template('index.html')

# Route für Whisper
@app.route('/transcribe_whisper', methods=['POST'])
def transcribe_with_whisper():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})

    try:
        # Konvertiere die Audiodatei
        wav_filename, debug_info = convert_audio(file.read())

        # Transkribiere mit Whisper
        result = whisper_model.transcribe(wav_filename)

        # Textkorrektur mit toolify
        corrected_text = toolify(result['text'])

        # Rückgabe des korrigierten Texts und der Debug-Informationen
        return jsonify({"corrected_text": corrected_text, **debug_info})
    except Exception as e:
        return jsonify({"error": f"Whisper transcription failed: {str(e)}"})

# Route für Vosk
@app.route('/transcribe_vosk', methods=['POST'])
def transcribe_with_vosk():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})

    try:
        # Konvertiere die Audiodatei
        wav_filename, debug_info = convert_audio(file.read())

        # Öffne die konvertierte WAV-Datei und transkribiere mit Vosk
        with wave.open(wav_filename, "rb") as wf:
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                return jsonify({"error": "Audio file must be WAV format mono PCM."})

            recognizer.AcceptWaveform(wf.readframes(wf.getnframes()))
            result = recognizer.Result()

        # Umwandlung des JSON-Strings in ein Dictionary
        result_dict = json.loads(result)

        # Textkorrektur mit toolify
        corrected_text = toolify(result_dict['text'])

        # Rückgabe des korrigierten Texts und der Debug-Informationen
        return jsonify({"corrected_text": corrected_text, **debug_info})
    except Exception as e:
        return jsonify({"error": f"Vosk transcription failed: {str(e)}"})

###########################################

@app.route('/transcribe_chunk', methods=['POST'])
def transcribe_chunk():
    if 'file' not in request.files or 'model' not in request.form:
        return jsonify({"error": "Invalid request"}), 400

    audio_file = request.files['file']
    selected_model = request.form['model']

    try:
        # Konvertiere die Audiodatei
        wav_filename, debug_info = convert_audio(audio_file.read())

        if selected_model == "vosk":
            # Verarbeite das Audio mit Vosk
            with wave.open(wav_filename, "rb") as wf:
                recognizer.AcceptWaveform(wf.readframes(wf.getnframes()))
                result = recognizer.Result()
                recognized_text = json.loads(result).get('text', '')
        elif selected_model == "whisper":
            # Verarbeite das Audio mit Whisper
            result = whisper_model.transcribe(wav_filename)
            recognized_text = result['text']
        else:
            return jsonify({"error": "Invalid model selected"}), 400

        return jsonify({"recognized_text": recognized_text, **debug_info})
    
    except Exception as e:
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500

##########################################

# Route zum Bereitstellen der HTML-Seite für Chunk-Aufnahmen
@app.route('/chunk_transcription')
def chunk_transcription():
    return render_template('chunk_transcription.html')


# Route zum Bereitstellen von statischen Dateien (z. B. CSS, JS)
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

####################################

# Start der Flask-App
if __name__ == '__main__':
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    app.run(host='0.0.0.0', port=5000)
