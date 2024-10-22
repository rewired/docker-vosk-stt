Download the appropiate model from https://alphacephei.com/vosk/models and place the content of model archive in `/models/vosk`

The model for whisper is currently downloaded automatically everytime the service is started...

```bash
docker build -t vosk-stt-service .
```

```bash
docker run -p 5000:5000 -v D:/__DEV/docker-vosk-stt:/app vosk-stt-service
```
After the service has started successfully you can point your browser to http://127.0.0.1:5000/
