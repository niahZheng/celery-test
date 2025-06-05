FROM python:3.10-slim

ENV NLTK_DATA=/usr/share/nltk_data

# Install NLTK and other dependencies
RUN pip install nltk

# Create a directory for NLTK data and download the 'punkt' resource
RUN mkdir -p $NLTK_DATA \
    && python -m nltk.downloader punkt -d $NLTK_DATA


WORKDIR /usr/src/app
COPY . .
RUN pip3 install -r requirements.txt

