FROM python:3.11-slim

# Install TeX Live minimal + TikZ/PGF + tools to convert PDF→PNG (transparent)
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base texlive-latex-extra texlive-pictures texlive-plain-generic \
    ghostscript poppler-utils ca-certificates bash \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Uvicorn on dynamic PORT (Render sets $PORT)
EXPOSE 10000
CMD ["bash","-lc","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
