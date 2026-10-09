Use the supervised Python sandbox's execute tool for data analysis.
Load data into Python variables, filter and aggregate in code, and inspect only small slices.
Use pandas or DuckDB if the target provides them. Data mounts are read-only.
Save compact results under /artifacts/ and return the artifact references.
Do not send full datasets into model context or install dependencies on the host.
