# Build: regenerate tables/macros/figures from manifests, then LaTeX.
PY ?= python3
all:
	cd .. && $(PY) scripts/make_tables.py && $(PY) scripts/make_figures.py
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	bibtex main
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.spl main.pdf
