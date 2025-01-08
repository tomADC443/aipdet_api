
FROM python:3.11.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/src

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]