`wordfreq.py` is a small CLI that prints word counts for a text file, one `word<TAB>count` per line,
sorted by count descending and then alphabetically. Add these features without breaking existing behaviour:

1. `--top N` prints only the first N lines (N must be a positive integer; otherwise exit with status 2).
2. `--ignore-case` counts words case-insensitively and prints them lowercased.
3. `--min-length L` ignores words shorter than L characters (default 1).
4. Reading from stdin when the path argument is `-`.

Also expose a function `count_words(text, ignore_case=False, min_length=1)` that returns a list of
`(word, count)` tuples in the same order the CLI prints them. A "word" is a maximal run of letters,
digits, or apostrophes (`[A-Za-z0-9']+`).
