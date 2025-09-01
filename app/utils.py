import base64
import os
import re
import subprocess
import pathlib

ALLOWED_PACKS = {
    "tikz", "pgfplots", "xcolor", "amsmath", "amssymb", "calc",
    "decorations.pathreplacing", "arrows.meta", "patterns",
    "shapes.geometric", "positioning"
}

def sanitize_packages(packages):
    out = []
    for p in packages or []:
        if re.fullmatch(r"[A-Za-z0-9_.\-]+", p) and p in ALLOWED_PACKS:
            out.append(p)
    if out:
        return "\n".join([fr"\usepackage{{{p}}}" for p in out])
    return ""

def safe_text(s: str, limit=120_000, allow_file_inputs: bool = False):
    """
    Lọc input cơ bản. Khi allow_file_inputs=True, cho phép \input/\include,
    nhưng CHẶN \write18, \openout, \read, \immediate\write.
    """
    s = s or ""
    if len(s) > limit:
        raise ValueError("Input quá dài.")
    low = s.lower()

    forbidden = [
        "\\write18",
        "\\openout",
        "\\read",
        "\\immediate\\write",
    ]
    if not allow_file_inputs:
        forbidden += ["\\input", "\\include"]

    for kw in forbidden:
        if kw in low:
            raise ValueError("Phát hiện lệnh LaTeX nhạy cảm: " + kw)

    # Dù cho phép \input/\include, vẫn CHẶN biến thể pipe: \input| ... / \include| ...
    # (pipe chỉ hiệu lực khi shell-escape bật; ta đã -no-shell-escape, nhưng vẫn chặn cho chắc)
    no_comments = strip_comments(s)
    if re.search(r'\\(?:input|include)\s*\|', no_comments):
        raise ValueError("Phát hiện dạng \\input| hoặc \\include| (bị chặn).")

    return s

def strip_comments(tex: str) -> str:
    """Bỏ phần sau '%' ở mỗi dòng (đơn giản mà hiệu quả cho scan)."""
    out = []
    for line in tex.splitlines():
        i = line.find('%')
        if i >= 0:
            line = line[:i]
        out.append(line)
    return "\n".join(out)

def run(cmd, cwd, timeout=60):
    proc = subprocess.run(
        cmd, cwd=cwd, timeout=timeout,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
    )
    return proc.returncode, proc.stdout.decode("utf-8", errors="ignore")

def compile_latex_to_pdf(tex_content: str, workdir: str):
    tex_file = pathlib.Path(workdir, "main.tex")
    tex_file.write_text(tex_content, encoding="utf-8")
    cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape", "main.tex"]
    code, log = run(cmd, cwd=workdir, timeout=120)
    pdf_path = pathlib.Path(workdir, "main.pdf")
    return code == 0 and pdf_path.exists(), log, str(pdf_path)

def pdf_to_png(pdf_path: str, out_prefix: str, dpi: int = 300, transparent=True):
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
