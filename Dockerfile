# Dockerfile (Debian slim) — hỗ trợ vietnam.sty, fontawesome, tkz-*
FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive

# TeX Live + fonts + language packs (có Vietnamese) + pdftocairo
# Chú ý:
# - texlive-fonts-extra: chứa fontawesome.sty
# - texlive-lang-other : chứa bộ vntex (Vietnamese)
# - texlive-latex-extra/recommended/pictures: nhiều gói bạn dùng (tikz, tkz-euclide, tkz-tab, titlesec, enumitem, etc.)
# - cm-super           : bộ font vector đầy đủ cho pdfLaTeX
# - poppler-utils      : có pdftocairo để chuyển PDF -> PNG
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        texlive-latex-base \
        texlive-latex-recommended \
        texlive-latex-extra \
        texlive-pictures \
        texlive-fonts-recommended \
        texlive-fonts-extra \
        texlive-lang-other \
        cm-super \
        poppler-utils \
        ca-certificates \
        bash; \
    rm -rf /var/lib/apt/lists/*

# Bảo đảm UTF-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code (có app/styles/ chứa vietnam.sty, ex_test.sty nếu bạn tự kèm)
COPY app ./app

# Render sẽ set PORT động
EXPOSE 10000
CMD ["bash","-lc","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
