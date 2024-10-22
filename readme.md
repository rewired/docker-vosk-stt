Down load the appropiate model from https://alphacephei.com/vosk/models and place the content of model archive in models/vosk

```bash
docker build -t vosk-stt-service .
```

```bash
docker run -p 5000:5000 -v D:/__DEV/docker-vosk-stt:/app vosk-stt-service
```
