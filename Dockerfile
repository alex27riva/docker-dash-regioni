FROM python:3.8-slim
LABEL maintainer "Alessandro Riva <alex27riva@gmail.com>"
WORKDIR /app
COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY ./ ./
EXPOSE 8050
CMD ["python", "./app.py"]
