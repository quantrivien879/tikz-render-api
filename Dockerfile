# Dockerfile (Debian slim)
FROM python:3.11-slim

# Tránh hỏi interactive khi cài apt
ARG DEBIAN_FRONTEND=noninteractive

# TeX Live tối thiểu + TikZ + fonts + language packs (có Vietnamese) + pdftocairo
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        texlive-latex-base \
        texlive-latex-extra \
        texlive-pictures \
        texlive-fonts-recommended \
        texlive-lang-other \ 
        cm-super \
        poppler-utils \
        ca-certificates \
        bash; \
    rm -rf /var/lib/apt/lists/*

# (tùy chọn) đảm bảo UTF-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY app ./app

# Render sẽ set PORT
EXPOSE 10000
CMD ["bash","-lc","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
