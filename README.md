# Jasnowidz
A site+scripts to see events from lublin

Currently only 3 sites scraping is implemented.

### Running frontend locally
Frontend made with astro, so it's easy to run it.
`cd Frontend/ && pnpm astro dev`
That's all

### Running backend scripts
First setup a pocketbase instance. App will work without it, but you won't be able to send the data to cloud, instead it will sit in the `data/` folder inside `Backend/`

Important folders:
- scripts/ - where scripts sit
- data/ - where output is saved
- config/ - where you can enable disable scrapers (doesn't enable disable scanning, just sending)

To run the app install uv, run `uv sync` and `uv run main.py`. Everything else is simple enough

### Ai disclosure
Some parts of code (like the labirynt datetime parser) were written by ai. Most code is human written, only a small percentage is written by ai. Smart autocomplete was used in making of the code

### Please do not scrape me
If you do not want your site to be scraped reach out at wife-cornmeal-lazy@duck.com and explain why do you not consent to your site to be scraped. I reccomend including a anti scraper policy in robots.txt.
