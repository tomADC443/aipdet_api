
FROM python:3.11.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/src

ENV PYTHONPATH=/code

CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8080"]