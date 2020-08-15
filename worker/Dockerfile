FROM tiangolo/uwsgi-nginx-flask:python3.8

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py /app
COPY logger.py /app
COPY context.py /app
COPY message.py /app
COPY modules /app/modules
COPY res /app/res

HEALTHCHECK CMD curl --fail http://localhost:80/worker || exit 1
