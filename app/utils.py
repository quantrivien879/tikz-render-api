import base64
import os
import re
import subprocess
import pathlib

# Cho phép một số gói phổ biến; có thể mở rộng theo nhu cầu
ALLOWED_PACKS = {
    "tikz", "pgfplots", "xcolor", "amsmath", "amssymb", "calc",
    "decorations.pathreplacing", "arrows.meta", "patterns",
    "shapes.geometric", "positioning"
}

def sanitize_packages(packages):
    """Lọc tên gói theo whitelist và ký tự hợp lệ."""
    out = []
    for p in packages or []:
        if re.fullmatch(r"[A-Za-z0-9_.\-]+", p) and p in ALLOWED_PACKS:
            out.append(p)
    # Tạo \usepackage{...} an toàn
    if out:
        return "\n".join([fr"\usepackage{{{p}}}" for p in out])
    return ""

def safe_text(s: str, limit=120_000):
    """Chặn input quá dài và một số lệnh LaTeX nguy hiểm (không regex)."""
    s = s or ""
    if len(s) > limit:
        raise ValueError("Input quá dài.")
    low = s.lower()
    # KHÔNG dùng docstring có backslash; dùng chuỗi bình thường/escaped
    forbidden = [
        "\\write18",
        "\\input",
        "\\include",
        "\\openout",
        "\\read",
        "\\immediate\\write"
    ]
    for kw in forbidden:
        if kw in low:
            raise ValueError("Phát hiện lệnh LaTeX nhạy cảm: " + kw)
    return s

def run(cmd, cwd, timeout=60):
    """Chạy tiến trình con và gom log/exit code."""
    proc = subprocess.run(
        cmd, cwd=cwd, timeout=timeout,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
    )
    return proc.returncode, proc.stdout.decode("utf-8", errors="ignore")

def compile_latex_to_pdf(tex_content: str, workdir: str):
    """Ghi main.tex và chạy pdflatex (không dùng shell-escape)."""
    tex_file = pathlib.Path(workdir, "main.tex")
    tex_file.write_text(tex_content, encoding="utf-8")
    cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape", "main.tex"]
    code, log = run(cmd, cwd=workdir, timeout=90)
    pdf_path = pathlib.Path(workdir, "main.pdf")
    return code == 0 and pdf_path.exists(), log, str(pdf_path)

def pdf_to_png(pdf_path: str, out_prefix: str, dpi: int = 300, transparent=True):
    # Dùng pdftocairo để xuất 1 ảnh PNG (có thể nền trong suốt)
    cmd = ["pdftocairo", "-png", "-singlefile", "-r", str(dpi)]
    if transparent:
        cmd.append("-transp")
    cmd.extend([pdf_path, out_prefix])
    code, log = run(cmd, cwd=os.path.dirname(pdf_path), timeout=60)
    out_file = f"{out_prefix}.png"
    return code == 0 and os.path.exists(out_file), log, out_file

def file_to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")
