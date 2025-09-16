# Makefile
PY=python3
OUT=out
SCRIPTS=scripts
DATA=data

TABLES=$(OUT)/table5_taxonomy_map_longtable_cited.tex \
       $(OUT)/table7_fidelity_system_evidence.tex

.PHONY: all tables pdf clean

all: tables pdf

tables: $(TABLES)

$(OUT)/table5_taxonomy_map_longtable_cited.tex: $(SCRIPTS)/build_tables.py $(DATA)/SLR_Summerization.xlsx
	@mkdir -p $(OUT)
	$(PY) $(SCRIPTS)/build_tables.py --excel $(DATA)/SLR_Summerization.xlsx --bibmap $(DATA)/bibkeys.csv --emit table5 --outdir $(OUT)

$(OUT)/table7_fidelity_system_evidence.tex: $(SCRIPTS)/build_tables.py $(DATA)/SLR_Summerization.xlsx
	@mkdir -p $(OUT)
	$(PY) $(SCRIPTS)/build_tables.py --excel $(DATA)/SLR_Summerization.xlsx --bibmap $(DATA)/bibkeys.csv --emit table7 --outdir $(OUT)

pdf: tables
	latexmk -pdf -bibtex -interaction=nonstopmode -outdir=$(OUT) main.tex

clean:
	latexmk -C -outdir=$(OUT)
	rm -f $(TABLES)
