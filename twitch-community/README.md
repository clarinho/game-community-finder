# Discord/Twitch Community Finder (with games!)

A Windows-friendly Python script that discovers **League of Legends** Twitch streams and prints clean, colorized results in a table. It also checks each streamer’s **Twitch About page** for **Discord invite links** (even if the streamer is offline when using name search).

## Features
 
- **Three discovery modes**
  - **Infinite discovery**: keep paging through live streams until you stop it
  - **Specify number of streams**: fetch a fixed number of live streams
  - **Search by name(s)**: look up specific channels and check Discord even if they’re offline
- **Sorting**
  - Viewers high → low
  - Viewers low → high
- **Viewer filters**
  - Min viewers
  - Max viewers
  - Saved between runs in a local config file
- **Discord scraping**
  - Scrapes Discord invites from the streamer’s `/about` page
  - Displays links in a normalized format
  - Includes colors for readability
- **Caching**
  - Stores Discord results in `discord_cache.json` to reduce repeated scraping

## Example Output
<img width="575" height="235" alt="WindowsTerminal_sIO41v9DcT" src="https://github.com/user-attachments/assets/37a99830-2be8-4bc6-8656-de1ca368029a" />

## Requirements
- Windows 10/11 recommended
- Python 3.10+ (3.11+ recommended)
- Google Chrome/Chromium + matching ChromeDriver
- Python packages:
  - `requests`
  - `selenium`

Install Python dependencies:

```bash
py -m pip install requests selenium
```
