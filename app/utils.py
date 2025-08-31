# app/utils.py
import base64, os, re, subprocess, pathlib

# Whitelist các gói cho phép nạp thêm (tuỳ bạn mở rộng)
ALLOWED_PACKS = {
    "tikz","pgfplots","xcolor","amsmath","amssymb","calc",
    "decorations.pathreplacing","arrows.meta","patterns",
    "shapes.geometric","positioning"
}

def sanitize_packages(packages):
    """
    Nhận list tên gói và chỉ giữ lại những gói hợp lệ trong whitelist.
    Trả về chuỗi \usepackage{...} theo từng dòng.
    """
    out = []
    for p in packages or []:
        if re.fullmatch(r"[A-Za-z0-9_.\-]+", p) and p in ALLOWED_PACKS:
            out.append(p)
    if out:
        return "\n".join([fr"\usepackage{{{p}}}" for p in out])
    return ""

def safe_text(s: str, limit=120_000):
    """
    Giới hạn độ dài & chặn một số lệnh nguy hiểm.
    """
    s = s or ""
    if len(s) > limit:
        raise ValueError("Input quá dài.")
    forbidden = [r"\write18", r"\input|", r"\include|", r"\openout", r"\read", r"\immediate\write"]
    for kw in forbidden:
        if kw in s:
            raise ValueError("Phát hiện lệnh LaTeX nhạy cảm.")
    return s

def _run(cmd, cwd, timeout=60):
    proc = subprocess.run(
        cmd, cwd=cwd, timeout=timeout,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
    )
    return proc.returncode, proc.stdout.decode("utf-8", errors="ignore")

def compile_latex_to_pdf(tex_content: str, workdir: str):
    """
    Ghi main.tex và chạy pdflatex (không shell-escape). Trả (ok, log, pdf_path).
    """
    tex_file = pathlib.Path(workdir, "main.tex")
    tex_file.write_text(tex_content, encoding="utf-8")
    cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape", "main.tex"]
    code, log = _run(cmd, cwd=workdir, timeout=90)
    pdf_path = pathlib.Path(workdir, "main.pdf")
    return code == 0 and pdf_path.exists(), log, str(pdf_path)

def pdf_to_png(pdf_path: str, out_prefix: str, dpi: int = 300, transparent=True):
    """
    Dùng pdftocairo chuyển PDF → PNG 1 trang, có thể nền trong suốt.
    """
    cmd = ["pdftocairo", "-png", "-singlefile", "-r", str(dpi)]
    if transparent:
        cmd.append("-transp")
    cmd.extend([pdf_path, out_prefix])
    code, log = _run(cmd, cwd=os.path.dirname(pdf_path))
    out_file = f"{out_prefix}.png"
    return code == 0 and os.path.exists(out_file), log, out_file

def file_to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")
