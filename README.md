# YouTube Transcript Extractor

Get a YouTube video's transcript as **copyable text** and a **CSV file**.

There are two ways to use this — pick whichever you like:

1. **Phone app (web app + Home Screen icon)** — `app.py` — recommended for iPhone.
2. **Command-line script** — `yt_transcript.py` — for a-Shell or any terminal.

Both share the same transcript logic, so they behave identically.

---

## Option 1 — Put it on your iPhone as an app

This turns the project into a web app with its own Home Screen icon. No Mac, no
App Store, no jailbreak. It takes about 5 minutes the first time.

### Step 1: Deploy it for free with Streamlit Community Cloud

1. Go to **https://share.streamlit.io** and sign in with your GitHub account
   (the same account that owns this repository).
2. Click **"Create app"** → **"Deploy a public app from GitHub"**.
3. Fill in:
   - **Repository:** this repository
   - **Branch:** `claude/youtube-transcript-extractor-atv0nx`
   - **Main file path:** `app.py`
4. Click **Deploy**. After a minute or two you'll get a public URL like
   `https://your-app-name.streamlit.app`.

(Streamlit reads `requirements.txt` automatically and installs everything.)

### Step 2: Add it to your Home Screen (iPhone)

1. Open that `.streamlit.app` URL in **Safari** (must be Safari, not Chrome).
2. Tap the **Share** button (the square with an arrow).
3. Scroll down and tap **"Add to Home Screen"**.
4. Name it (e.g. *Transcripts*) and tap **Add**.

You now have an app icon. Tapping it opens the tool full-screen, like a real app.

### Step 3: Use it

Paste a YouTube link, tap **Get transcript**, then copy the text or download the
CSV / text file (iOS saves downloads via the Files app or the Share sheet).

> **Heads-up about free hosting:** YouTube sometimes blocks transcript requests
> coming from shared cloud servers. If you ever see a "temporarily blocked"
> message, wait a bit and retry, or use the command-line version (Option 2),
> which runs from your own phone's connection and is rarely blocked.

---

## Option 2 — Command-line script (a-Shell)

Install the one library it needs (run once):

```
pip install youtube-transcript-api
```

Then run it, either letting it prompt you:

```
python yt_transcript.py
```

or passing the URL directly (keep the quotes):

```
python yt_transcript.py "https://youtu.be/dQw4w9WgXcQ"
```

It saves a `<video_id>.csv` to the current folder and prints a clean
`[mm:ss] text` transcript you can select and copy.

---

## Optional: using a proxy (if YouTube blocks the server)

You do **not** need this to use the tool. It only matters if you see a
"temporarily blocked" message, which can happen on free cloud hosting because
YouTube rate-limits shared server IPs.

**Honest note:** a proxy that reliably gets past YouTube's blocking is normally
a *residential* proxy, which costs money. Free public proxies are usually dead,
slow, or unsafe — so this is an option, not a guaranteed fix. The proxy support
itself is free and built in; if you don't set one, nothing changes.

If you do have a proxy URL, set it in whichever way matches how you're running:

- **Command-line (a-Shell / terminal):**
  ```
  export YT_PROXY="http://user:pass@host:port"
  python yt_transcript.py "https://youtu.be/VIDEOID"
  ```

- **Web app (Streamlit), two ways:**
  - Quick: tap **"Advanced: use a proxy (optional)"** in the app and paste it.
  - Permanent: in your Streamlit Community Cloud app, open
    **Settings → Secrets** and add a line:
    ```
    YT_PROXY = "http://user:pass@host:port"
    ```

---

## Supported link formats

Both versions understand: `youtube.com/watch?v=…`, `youtu.be/…`,
`youtube.com/shorts/…`, `embed/…`, `live/…`, `m.`/`music.` subdomains, and
links with extra query params like `&t=` and `&list=`.
