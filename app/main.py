# app/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import tempfile
import pathlib
import shutil
import os

from .tex_templates import BASE_PREAMBLE, DOC_WRAP, TIKZ_ENV_WRAP
from .utils import (
    sanitize_packages,
    safe_text,
    compile_latex_to_pdf,
    pdf_to_png,
    file_to_b64,
    run,
)

# ---------- FastAPI app ----------
app = FastAPI(title="TikZ/LaTeX Render API", version="1.1.0")

# Cho phép gọi từ Apps Script / trình duyệt
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # Có thể siết domain nếu cần
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Models cho /compile (TikZ) ----------
class CompileRequest(BaseModel):
    source: str = Field(..., description="Nội dung TikZ hoặc full LaTeX.")
    mode: str = Field("auto", description="'auto'|'body'|'full'")
    format: str = Field("png", description="'png'|'pdf'")
    density: int = Field(300, ge=72, le=600, description="DPI cho PNG")
    packages: Optional[List[str]] = Field(default=None, description="Các gói được whitelist")
    preamble: Optional[str] = Field(default="", description="Preamble bổ sung (tùy chọn)")
    transparent: bool = True
    return_log: bool = False


class CompileResponse(BaseModel):
    ok: bool
    image_base64: Optional[str] = None
    pdf_base64: Optional[str] = None
    log: Optional[str] = None


# ---------- Models cho /compile-tex (full .tex) ----------
class TexAsset(BaseModel):
    filename: str = Field(..., description="Tên file kèm (ví dụ: Img-1.png)")
    base64: str = Field(..., description="Dữ liệu base64 của file kèm")


class TexCompileRequest(BaseModel):
    tex: str = Field(..., description="Toàn bộ nội dung .tex (đã có \\documentclass ...)")
    engine: str = Field("pdflatex", description="'pdflatex' (khuyên dùng).")
    return_log: bool = False
    assets: Optional[List[TexAsset]] = None  # Ảnh/tài nguyên đi kèm (nếu có)


class TexCompileResponse(BaseModel):
    ok: bool
    pdf_base64: Optional[str] = None
    log: Optional[str] = None


# ---------- Helpers ----------
def _styles_dir() -> pathlib.Path:
    # app/styles/
    return pathlib.Path(__file__).parent / "styles"


def _copy_all_styles(dst_dir: str):
    """
    Copy toàn bộ file .sty trong app/styles vào thư mục biên dịch tạm.
    Hỗ trợ các gói tùy biến như vietnam.sty, ex_test.sty, ...
    """
    src_dir = _styles_dir()
    if not src_dir.exists():
        return
    for p in src_dir.iterdir():
        if p.is_file() and p.suffix.lower() == ".sty":
            shutil.copy(str(p), os.path.join(dst_dir, p.name))


def _safe_filename(name: str) -> str:
    name = os.path.basename(name or "")
    if not name or len(name) > 180 or any(c in name for c in '\\:*?"<>|'):
        raise ValueError(f"Tên file không hợp lệ: {name}")
    return name


def _is_full_document(s: str) -> bool:
    return "\\documentclass" in s


# ---------- Routes ----------
@app.get("/")
def health():
    return {"status": "ok", "service": "tikz-latex-render-api", "version": "1.1.0"}


@app.post("/compile", response_model=CompileResponse)
def compile_tikz(req: CompileRequest):
    """
    Biên dịch TikZ → PNG/PDF.
    - mode = 'full': coi source là toàn bộ tài liệu LaTeX (đã có \documentclass)
    - mode = 'body' hoặc 'auto' (mặc định): wrap vào standalone + tikz
    - format = png: dùng pdftocairo để chuyển PDF → PNG nền trong suốt (tuỳ chọn)
    """
    try:
        src = safe_text(req.source)
        extra_packs = sanitize_packages(req.packages)
        extra_preamble = safe_text(req.preamble or "", limit=10_000)

        # Build LaTeX nội bộ
        preamble = BASE_PREAMBLE.replace("{EXTRA_PACKAGES}", extra_packs)\
                                .replace("{EXTRA_PREAMBLE}", extra_preamble)

        if req.mode == "full" or (req.mode == "auto" and _is_full_document(src)):
            # Người dùng đã gửi full document → dùng nguyên văn
            tex = src
        else:
            # Wrap vào standalone
            if "\\begin{tikzpicture}" in src:
                body = src
            else:
                body = TIKZ_ENV_WRAP.replace("{CONTENT}", src)
            tex = DOC_WRAP.replace("{PREAMBLE}", preamble).replace("{BODY}", body)

        with tempfile.TemporaryDirectory() as td:
            # Copy tất cả .sty tùy biến (vietnam.sty, ex_test.sty, …)
            _copy_all_styles(td)

            ok, log, pdf_path = compile_latex_to_pdf(tex, td)
            if not ok:
                raise HTTPException(status_code=400, detail=f"Biên dịch LaTeX lỗi.\n{log[:8000]}")

            if req.format == "pdf":
                return CompileResponse(ok=True, pdf_base64=file_to_b64(pdf_path), log=(log if req.return_log else None))

            # PNG
            out_prefix = str(pathlib.Path(td, "page"))
            ok_png, log_png, png_path = pdf_to_png(pdf_path, out_prefix, dpi=req.density, transparent=req.transparent)
            if not ok_png:
                raise HTTPException(status_code=500, detail=f"Chuyển PDF→PNG lỗi.\n{log_png[:8000]}")
            full_log = (log + "\n" + log_png) if req.return_log else None
            return CompileResponse(ok=True, image_base64=file_to_b64(png_path), log=full_log)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {e}")


@app.post("/compile-tex", response_model=TexCompileResponse)
def compile_tex(req: TexCompileRequest):
    """
    Biên dịch toàn bộ tài liệu LaTeX (.tex đầy đủ) → PDF.
    - Tự copy mọi .sty trong app/styles/ vào thư mục tạm (hỗ trợ vietnam.sty, ex_test.sty, ...)
    - Hỗ trợ đính kèm assets (ảnh, v.v.) qua base64 nếu tài liệu có \includegraphics{...}
    """
    try:
        src = safe_text(req.tex, limit=500_000, allow_file_inputs=True)

        engine = (req.engine or "pdflatex").strip().lower()
        if engine not in {"pdflatex"}:
            engine = "pdflatex"

        styles_dir = _styles_dir()
        if not styles_dir.exists():
            # không bắt buộc, nhưng cảnh báo nhẹ nếu bạn kỳ vọng có các .sty custom
            pass

        with tempfile.TemporaryDirectory() as td:
            # 1) Copy tất cả .sty tùy biến
            _copy_all_styles(td)

            # 2) Nếu có assets (ảnh, v.v.)
            if req.assets:
                import base64
                for it in req.assets:
                    fname = _safe_filename(it.filename)
                    data = base64.b64decode(it.base64.encode("ascii"))
                    open(os.path.join(td, fname), "wb").write(data)

            # 3) Ghi main.tex
            main_tex = os.path.join(td, "main.tex")
            pathlib.Path(main_tex).write_text(src, encoding="utf-8")

            # 4) Biên dịch (không shell-escape)
            cmd = [engine, "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape", "main.tex"]
            code, log = run(cmd, cwd=td, timeout=180)
            pdf_path = os.path.join(td, "main.pdf")

            if code != 0 or not os.path.exists(pdf_path):
                raise HTTPException(status_code=400, detail=f"Biên dịch LaTeX lỗi.\n{log[:10000]}")

            return TexCompileResponse(ok=True, pdf_base64=file_to_b64(pdf_path), log=(log if req.return_log else None))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {e}")
