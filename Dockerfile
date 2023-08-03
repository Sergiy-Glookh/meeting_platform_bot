FROM python:3.10-slim-buster

WORKDIR .

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "src/user_bot.py"]
