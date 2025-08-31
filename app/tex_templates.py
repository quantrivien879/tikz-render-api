BASE_PREAMBLE = r"""
\documentclass[tikz]{standalone}
\usepackage{amsmath, amssymb}
\usepackage{tikz}
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

TIKZ_ENV_WRAP = r"""
\begin{tikzpicture}
{CONTENT}
\end{tikzpicture}
"""
