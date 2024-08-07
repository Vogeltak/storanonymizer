FROM python:3.11

EXPOSE 5000

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./deploy.py" ]
