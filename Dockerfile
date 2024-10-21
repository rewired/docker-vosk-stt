FROM python:3.9-slim

WORKDIR /app

COPY /.cache/whisper/ /root/.cache/whisper/
COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y ffmpeg

RUN pip install pydub
RUN pip install openai-whisper
RUN pip install ffmpeg-python

COPY . .

EXPOSE 5000

CMD ["python", "server.py"]