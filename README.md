# ecgmeans.com

Static site for **ECG Means** — plain-English explanations of the phrases printed on ECG/EKG
reports, reviewed by Dr. Faisal Irshad, MBBS (PMDC 54440-S). 82 pages, including 4 ECG calculators
and a schematic ECG illustration on every finding page.

## Structure
- Pre-built static HTML (one `index.html` per directory) at the repo root.
- `content/` + `build.py` + `make_assets.py` are the generator (blocked from the web by `.htaccess` + `robots.txt`).

## Build locally
```
pip install markdown pillow --break-system-packages
./build.sh   # from the parent build folder: runs build.py + make_assets.py and preserves .git/.github
```
Generator files: `build.py` (pages, schema, sitemap, llms.txt), `ecg_svg.py` (ECG illustrations), `make_assets.py` (CSS, icons).
```
```

## Deploy
Push to `main`; the GitHub Action triggers a Cloudways git pull (server 1638726, app 6684252) and purges cache.
Requires repo secrets `CLOUDWAYS_EMAIL` and `CLOUDWAYS_API_KEY`. The workflow waits for the pull, purges Varnish,
verifies the live site is fresh, then pings IndexNow (Bing/Yandex) with every sitemap URL.
