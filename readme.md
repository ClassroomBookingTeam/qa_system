# QA System

Вопросы задаются в формате json, внутри файла db.json.

Программа запускается с помощью

```sh
pip install -r requirements.txt
python main.py
```

Для запуска должны быть развернуты endpoint'ы сервисов транскрибирования и RH_VOICE_test.
При необходимости url endpoint можно поменять в коде.

```
POST /qa_text file=... - возвращает json {"question": "...", "answer": "..." }
POST /qa_voice file=... - возвращает аудиофайл ответа на вопрос
```