FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY telethon_helper.py ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

HEALTHCHECK CMD ps cax | grep python | grep -o '^[ ]*[0-9]*' && exit 0 || exit 1

CMD [ "python3", "./app.py" ]