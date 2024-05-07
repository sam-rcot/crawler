## Script to export and parse URL aliases and redirects

### Clone the repository and run:
    conda env create --name crawler --file environment.yml
    conda activate crawler

### To create a CSV with URL aliases run:
    python src/crawler.py
    python src/process_aliases.py

### To create a CSV with URL redirects run:
    python src/crawler_redirects.py
    python src/process_redirects.py

### After this run:
    python src/combine.py
    python src/process_all.py

### To fine-tune the list of redirects and aliases:
Edit the `filter_data()` function in `process_all.py`
