# Jasnowidz - Lublin event scraping
This is a collection of scripts meant to simplify finding events in the city (and near) Lublin. 
App is separated into a few parts: 
  - scrapers/ folder with the individual scripts for sites 
  - main.py which is a central place for selecting actions 
  - data/ where local scraped data is saved before uploading to cloud 
  - utils/ with helper functions

To-do:
* [ ] Add dev enviroment detecton
  * [ ] Add caching pages to not spam websites with requests
* [ ] Add console commands for automating production deployment
* [ ] Add predefined scripts like scan all & that are useful to be ran on cron jobs
* [ ] Write extensive docs
  * [ ] Alternative: write good enough docs
