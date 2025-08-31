BASE_PREAMBLE = r"""
\documentclass[tikz]{standalone}
\usepackage{amsmath, amssymb}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
% --- Add-ons here ---
{EXTRA_PACKAGES}
{EXTRA_PREAMBLE}
"""

DOC_WRAP = r"""
{PREAMBLE}
\begin{document}
{BODY}
\end{document}
"""

# If user sends pure tikz body lines (no \begin{tikzpicture})
TIKZ_ENV_WRAP = r"""
\begin{tikzpicture}
{CONTENT}
\end{tikzpicture}
"""
