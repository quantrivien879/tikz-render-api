from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import tempfile, pathlib

from .tex_templates import BASE_PREAMBLE, DOC_WRAP, TIKZ_ENV_WRAP
from .utils import sanitize_packages, safe_text, compile_latex_to_pdf, pdf_to_png, file_to_b64

app = FastAPI(title="TikZ Render API", version="1.0.0")

# CORS: cho phép gọi từ Apps Script/HTMLService
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # siết lại domain của bạn nếu muốn
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CompileRequest(BaseModel):
    source: str = Field(..., description="Nội dung TikZ hoặc full LaTeX.")
    mode: str = Field("auto", description="'auto'|'body'|'full'")
    format: str = Field("png", description="'png'|'pdf'")
    density: int = Field(300, ge=72, le=600, description="DPI cho PNG")
    packages: Optional[List[str]] = Field(default=None, description="Các gói được whitelist")
    preamble: Optional[str] = Field(default="", description="Preamble bổ sung (an toàn, ngắn gọn)")
    transparent: bool = True
    return_log: bool = False

class CompileResponse(BaseModel):
    ok: bool
    image_base64: Optional[str] = None
    pdf_base64: Optional[str] = None
    log: Optional[str] = None

@app.get("/")
def health():
    return {"status": "ok", "service": "tikz-render-api"}

@app.post("/compile", response_model=CompileResponse)
def compile_tikz(req: CompileRequest):
    try:
        src = safe_text(req.source)
        extra_packs = sanitize_packages(req.packages)
        extra_preamble = safe_text(req.preamble or "", limit=10_000)

        # Build LaTeX content
        def is_full_document(s: str) -> bool:
            return "\\documentclass" in s

        preamble = BASE_PREAMBLE.replace("{EXTRA_PACKAGES}", extra_packs)\
                                .replace("{EXTRA_PREAMBLE}", extra_preamble)

        if req.mode == "full" or (req.mode == "auto" and is_full_document(src)):
            body = src
            tex = body  # already full doc
        else:
            # 'auto' or 'body' → wrap into standalone document
            if "\\begin{tikzpicture}" in src:
                body = src
            else:
                body = TIKZ_ENV_WRAP.replace("{CONTENT}", src)
            tex = DOC_WRAP.replace("{PREAMBLE}", preamble).replace("{BODY}", body)

        with tempfile.TemporaryDirectory() as td:
            ok, log, pdf_path = compile_latex_to_pdf(tex, td)
            if not ok:
                raise HTTPException(status_code=400, detail=f"Biên dịch LaTeX lỗi.\n{log[:5000]}")

            if req.format == "pdf":
                return CompileResponse(ok=True, pdf_base64=file_to_b64(pdf_path), log=(log if req.return_log else None))

            # PNG
            out_prefix = str(pathlib.Path(td, "page"))
            ok_png, log_png, png_path = pdf_to_png(pdf_path, out_prefix, dpi=req.density, transparent=req.transparent)
            if not ok_png:
                raise HTTPException(status_code=500, detail=f"Chuyển PDF→PNG lỗi.\n{log_png[:5000]}")
            return CompileResponse(ok=True, image_base64=file_to_b64(png_path),
                                   log=(log + "\n" + log_png if req.return_log else None))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {e}")
