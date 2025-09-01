# Dockerfile
FROM python:3.11-slim

# Cài TeX Live tối thiểu + TikZ + tiếng Việt + font + công cụ PDF→PNG
# Ghi chú:
# - texlive-lang-vietnamese: gói hỗ trợ tiếng Việt (vntex, T5 encoding, v.v.)
# - texlive-fonts-recommended: font cơ bản (Latin Modern, etc.)
# - cm-super: bộ font vector đầy đủ cho pdfLaTeX khi cần (to hơn, nhưng an toàn)
# - poppler-utils: có pdftocairo dùng để xuất PNG nền trong suốt
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-pictures \
    texlive-fonts-recommended \
    texlive-lang-vietnamese \
    cm-super \
    poppler-utils \
    ca-certificates \
    bash \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# (tuỳ chọn) đảm bảo môi trường UTF-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

WORKDIR /app

# Cài Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY app ./app

# Render sẽ đặt $PORT động
EXPOSE 10000
CMD ["bash","-lc","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
