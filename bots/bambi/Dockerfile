FROM python:3.11-slim

WORKDIR /app

COPY bots/bambi/ /app/
COPY main_cogs.py /app/
COPY helper_files/ /app/helper_files/
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bambi_bot.py"]

