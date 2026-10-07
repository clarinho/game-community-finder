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
pip install requests selenium
```

# Twitch Community Finder

A command-line tool for discovering Twitch streamers and locating Discord communities associated with their channels.

The application can:

- Browse live Twitch streams
- Filter streams by viewer count
- Search for specific Twitch users
- Check whether users are live or offline
- Find Discord invite links from Twitch channel pages
- Look up channels followed by your Twitch account
- Cache Discord results to reduce repeated scraping

## Requirements

Before starting, install:

- **Python 3.10+**
- **Google Chrome**
- **ChromeDriver**
- A **Twitch account**
- A **Twitch Developer application**
- **Python Packages:**
  - `requests`
  - `selenium`

Git is also recommended if you are cloning the repository.

---

## 1. Clone the Repository

Open PowerShell, Command Prompt, or a terminal:

```bash
git clone https://github.com/clarinho/game-community-finder.git
cd game-community-finder/twitch-community
```

---

## 2. Create a Python Virtual Environment

Creating a virtual environment is recommended so the project's packages do not interfere with other Python installations.

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should now see something similar to:

```text
(.venv)
```

at the beginning of your terminal prompt.

---

## 3. Install Python Dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

The main dependencies are:

- `requests`
- `selenium`

---

## 4. Install Google Chrome

The Discord-finding portion of the program uses Selenium to inspect Twitch channel pages, so Google Chrome must be installed.

Download Chrome from:

https://www.google.com/chrome/

If Chrome is already installed, you can skip this step.

---

## 5. Install ChromeDriver

This project currently expects the path to a ChromeDriver executable in its configuration.

Download a ChromeDriver version compatible with your version of Chrome:

https://googlechromelabs.github.io/chrome-for-testing/

Extract `chromedriver.exe` somewhere permanent.

For example:

```text
C:\WebDriver\chromedriver.exe
```

You will need this path later.

You will also need the path to your Chrome executable.

A common Windows Chrome location is:

```text
C:\Program Files\Google\Chrome\Application\chrome.exe
```

Your installation may be somewhere else.

---

# Twitch API Setup

## 6. Create a Twitch Developer Application

Go to the Twitch Developer Console:

https://dev.twitch.tv/console/apps

Log in with your Twitch account.

Twitch requires developer accounts to have **two-factor authentication enabled**.

Choose:

```text
Register Your Application
```

Enter an application name. For example:

```text
Twitch Community Finder
```

For the OAuth Redirect URL, you can use:

```text
http://localhost:3000
```

Choose an appropriate category and create the application.

After creating it, open **Manage** for the application.

You will need two values:

- **Client ID**
- **Client Secret**

Click **New Secret** to generate a client secret.

> **Never commit your Client Secret to GitHub.**

The Client ID is not considered secret, but this project stores both values together in a local secrets file for convenience.

---

## 7. Create `secrets.json`

Inside the `twitch-community` directory—the same directory containing `main.py`—create:

```text
secrets.json
```

Your directory should look roughly like:

```text
twitch-community/
├── community_finder/
├── config.json
├── filters.json
├── main.py
├── requirements.txt
├── secrets.json
└── .gitignore
```

Put the following inside `secrets.json`:

```json
{
  "TWITCH_CLIENT_ID": "YOUR_TWITCH_CLIENT_ID",
  "TWITCH_CLIENT_SECRET": "YOUR_TWITCH_CLIENT_SECRET",
  "CHROME_BINARY_PATH": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "CHROMEDRIVER_PATH": "C:\\WebDriver\\chromedriver.exe"
}
```

Replace the placeholder Twitch values with the credentials from your Twitch Developer application.

### Important note for Windows paths

JSON requires backslashes to be escaped.

This is correct:

```json
"C:\\WebDriver\\chromedriver.exe"
```

This is not:

```json
"C:\WebDriver\chromedriver.exe"
```

---

## 8. Protect Local Credentials and Tokens

Make sure `.gitignore` contains:

```gitignore
secrets.json
user_token.json
discord_cache.json
__pycache__/
*.pyc
.venv/
```

`secrets.json` contains your Twitch application secret.

`user_token.json` is automatically created when you authorize your Twitch account for features that require user access. It contains OAuth credentials and **must not be committed to GitHub**.

If either file is accidentally committed to a public repository, consider the credentials compromised and revoke/regenerate them.

---

# Running the Program

## 9. Start the Application

From inside:

```text
game-community-finder/twitch-community
```

run:

```bash
python main.py
```

On systems where Python is invoked as `python3`, use:

```bash
python3 main.py
```

You should see a menu similar to:

```text
=== Twitch Finder ===

[1] Infinite discovery
[2] Specify number of streams
[3] Search by name(s)
[4] Filter Config
[5] Performance Config
[6] Followed channels lookup (requires Twitch login)
[7] Exit
```

---

# Twitch Account Authorization

Most features use an application access token and do **not** require you to log into Twitch manually.

The **Followed channels lookup** feature is different because reading your followed channels requires permission from your Twitch account.

Select:

```text
[6] Followed channels lookup
```

The first time you use it, the program will display something similar to:

```text
=== Twitch Authorization Required ===
Open: https://www.twitch.tv/activate
Enter code: XXXXXXXX
```

Open the displayed URL in your browser, enter the provided code if necessary, and approve access.

The application requests:

```text
user:read:follows
```

This allows it to retrieve channels followed by the authorized Twitch account.

After authorization, Twitch returns an access token and refresh token. The program stores these locally in:

```text
user_token.json
```

Do **not** upload this file to GitHub.

Future runs will attempt to refresh the token automatically.

---

# Configuration

## Viewer Filters

Viewer-count filtering can be changed from the application's **Filter Config** menu.

The values are stored in:

```text
filters.json
```

Example:

```json
{
  "min_viewers": 0,
  "max_viewers": 100000
}
```

---

## Performance Settings

Performance and scraping settings can be changed from the application's **Performance Config** menu.

They are stored in:

```text
config.json
```

The available settings include:

- `PAGE_LOAD_TIMEOUT_SECONDS`
- `DISCORD_WAIT_SECONDS`
- `DISCORD_POLL_INTERVAL_SECONDS`
- `PAGE_LOAD_STRATEGY`
- `SCRAPE_WORKERS`
- `SCRAPE_TIMEOUT_PER_CHANNEL`
- `STREAMS_PAGE_SIZE`
- `VERBOSE`
- `CACHE_EMPTY_RESULTS`

The defaults should work for most users.

If Twitch pages fail to load reliably, increasing `PAGE_LOAD_TIMEOUT_SECONDS` or `DISCORD_WAIT_SECONDS` may help.

---

# Discord Detection

The program attempts to find Discord invite links from Twitch channel About pages.

It recognizes links such as:

```text
discord.gg/example
discord.com/invite/example
discordapp.com/invite/example
```

Selenium launches Chrome in **headless mode**, so Chrome windows normally will not appear while channels are being checked.

Results are cached locally in:

```text
discord_cache.json
```

This file can safely be deleted if you want the program to re-check channels.

---

# Updating

Pull the newest version:

```bash
git pull
```

Then update dependencies:

```bash
pip install -r requirements.txt
```

---

# Troubleshooting

## `Missing secrets file`

If you see an error mentioning:

```text
Missing secrets file
```

make sure `secrets.json` exists directly inside:

```text
twitch-community/
```

and not inside:

```text
twitch-community/community_finder/
```

---

## ChromeDriver fails to start

Check that:

```json
"CHROME_BINARY_PATH"
```

points to your actual Chrome executable and:

```json
"CHROMEDRIVER_PATH"
```

points to your actual ChromeDriver executable.

Also make sure the ChromeDriver version is compatible with your installed version of Chrome.

---

## Twitch API authentication fails

Verify that your `secrets.json` contains the current:

```text
TWITCH_CLIENT_ID
TWITCH_CLIENT_SECRET
```

from your Twitch Developer Console.

If you generated a **new Twitch Client Secret**, the previous secret is invalid and `secrets.json` must be updated.

---

## Followed channels authorization fails

Delete:

```text
user_token.json
```

and run the followed-channels feature again.

The program will start a fresh Twitch authorization flow and create a new token file.

---

# Security

Never commit any of the following:

```text
secrets.json
user_token.json
```

Before pushing changes, it is a good idea to run:

```bash
git status
```

and verify that neither file appears under files to be committed.

If a Twitch client secret, access token, or refresh token is ever pushed to a public GitHub repository, **deleting the file afterward is not sufficient**. Revoke or regenerate the exposed credential because it may still exist in Git history.
