# ecgmeans.com

Static site for **ECG Means** — plain-English explanations of the phrases printed on ECG/EKG
reports, reviewed by Dr. Faisal Irshad, MBBS (PMDC 54440-S). 77 pages.

## Structure
- Pre-built static HTML (one `index.html` per directory) at the repo root.
- `content/` + `build.py` + `make_assets.py` are the generator (blocked from the web by `.htaccess` + `robots.txt`).

## Build locally
```
pip install markdown pillow --break-system-packages
python3 build.py && python3 make_assets.py   # NOTE: build.py wipes/recreates the output (repo root)
```

## Deploy
Push to `main`; the GitHub Action triggers a Cloudways git pull (server 1638726, app 6684252) and purges cache.
Requires repo secrets `CLOUDWAYS_EMAIL` and `CLOUDWAYS_API_KEY`.
