FROM python:3.10-alpine3.21
LABEL author="chu3an@github"

RUN pip install flask requests

WORKDIR /app
COPY app.py /app/

EXPOSE 9080
CMD ["python", "/app/app.py"]
