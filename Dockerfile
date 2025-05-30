FROM python:3.10.7-slim

RUN apt-get update && apt-get install -y \
build-essential \
libglib2.0-0 \
libsm6 \
libxrender1 \
libxext6 \
git \
wget \
&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip 
RUN pip install --no-cache-dir -r requirements.txt 
RUN pip install --no-cache-dir git+https://github.com/facebookresearch/fastText.git

RUN python -m nltk.downloader -d /usr/local/nltk_data punkt stopwords
ENV NLTK_DATA=/usr/local/nltk_data

COPY . .
COPY swagger/dist ./swagger/dist
COPY openapi.yaml ./openapi.yaml

EXPOSE 5000

ENV FLASK_APP=app.main:create_app
ENV FLASK_ENV=development

CMD ["flask", "run", "--host=0.0.0.0"]