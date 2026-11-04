# Local data policy

No raw data is stored in this repository. Download the official dataset from https://doi.org/10.5281/zenodo.19755088 (CC BY 4.0), record its MD5, inspect it with `chemiproof dataset inspect-zip`, and extract the `.dat` folders to `data/raw/extracted/` (git-ignored). `chemiproof dataset audit` then writes the manifest to `data/interim/` (git-ignored). Synthetic test fixtures are generated in code (`src/chemiproof/data/synthetic.py`).
