BASE_PREAMBLE = r"""
\documentclass[tikz]{standalone}
\usepackage{amsmath, amssymb}
\usepackage{tikz,tkz-tab}
\usetikzlibrary{shapes,shapes.geometric,arrows,calc,intersections,angles,patterns,arrows,decorations.pathmorphing,backgrounds,positioning,fit,petri,shapes.symbols,matrix,tikzmark}
\usetikzlibrary{positioning,decorations.text,decorations.pathmorphing}% Để uốn cong văn bản
\usetikzlibrary{shadings,fadings} %ĐỔ BÓNG
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
