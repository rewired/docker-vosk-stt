docker build -t vosk-stt-service .
docker run -p 5000:5000 -v D:/__DEV/docker-vosk-stt:/app vosk-stt-service