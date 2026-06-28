#!/usr/bin/env python3
# =============================================================================
# YouTube Transcript Extractor  --  built for a-Shell on iPhone
# =============================================================================
#
# WHAT THIS DOES
#   You give it a YouTube link. It downloads the video's captions (subtitles)
#   and gives you back two things:
#     1) A CSV file saved next to this script, named after the video ID,
#        with two columns:  timestamp_mm_ss , text
#     2) A clean, copy-pasteable transcript printed to the screen, where every
#        line starts with a [mm:ss] timestamp.
#
# -----------------------------------------------------------------------------
# STEP 0 -- INSTALL THE ONE LIBRARY THIS NEEDS (run this ONCE in a-Shell)
# -----------------------------------------------------------------------------
#
#     pip install youtube-transcript-api
#
#   After that finishes, run the script with either:
#
#     python yt_transcript.py
#       (it will then ask you to paste a URL)
#
#   ...or paste the URL right on the command line:
#
#     python yt_transcript.py "https://youtu.be/dQw4w9WgXcQ"
#
# =============================================================================

# --- Standard library imports (these come with Python, nothing to install) ---
import sys          # lets us read command-line arguments and exit cleanly
import re           # "regular expressions" -- used to pull the video ID out of a URL
import csv          # writes the CSV file for us, with correct quoting
from urllib.parse import urlparse, parse_qs   # safely takes a URL apart


# =============================================================================
# SECTION 1 -- Turn a YouTube URL into a "video ID"
# =============================================================================
# Every YouTube video has an 11-character ID (e.g. dQw4w9WgXcQ). The same video
# can be linked in many different URL shapes, so this function understands all
# of the common ones and returns just that ID.

def extract_video_id(url):
    """Return the 11-char YouTube video ID found in `url`, or None if there
    isn't one we recognize."""

    url = url.strip()  # remove stray spaces/newlines from a copy-paste

    # If the user pasted just the bare ID by itself, accept it as-is.
    # (A valid ID is 11 characters: letters, digits, dash, underscore.)
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", url):
        return url

    # Make sure urlparse treats it as a real URL even if "https://" is missing.
    if not re.match(r"^https?://", url):
        url = "https://" + url

    parsed = urlparse(url)                 # break the URL into pieces
    host = parsed.netloc.lower()           # e.g. "www.youtube.com" or "youtu.be"
    path = parsed.path                      # e.g. "/watch" or "/shorts/<id>"

    # --- Case A: short links like  youtu.be/<id>  ---
    if "youtu.be" in host:
        # The ID is the first chunk of the path, after the leading "/".
        candidate = path.lstrip("/").split("/")[0]
        if re.fullmatch(r"[0-9A-Za-z_-]{11}", candidate):
            return candidate

    # --- Case B: any youtube.com domain (www., m., music., etc.) ---
    if "youtube.com" in host:
        # B1: standard watch links  ->  youtube.com/watch?v=<id>&t=...&list=...
        #     The ID lives in the "v" query parameter; extra params are ignored.
        query = parse_qs(parsed.query)     # turns "v=ABC&t=5s" into {"v":["ABC"], "t":["5s"]}
        if "v" in query:
            candidate = query["v"][0]
            if re.fullmatch(r"[0-9A-Za-z_-]{11}", candidate):
                return candidate

        # B2: path-based links  ->  /shorts/<id>, /embed/<id>, /v/<id>, /live/<id>
        m = re.match(r"^/(?:shorts|embed|v|live)/([0-9A-Za-z_-]{11})", path)
        if m:
            return m.group(1)

    # If nothing matched, we couldn't find a valid ID.
    return None


# =============================================================================
# SECTION 2 -- Fetch the captions for a given video ID
# =============================================================================
# This uses the `youtube-transcript-api` library. That library has changed its
# function names across versions, so we try the newer style first and fall back
# to the older style. Either way we end up with a simple list of caption pieces,
# each having: text, start (seconds), duration (seconds).

def fetch_transcript(video_id):
    """Return a list of dicts like {'text': ..., 'start': ..., 'duration': ...}.
    Raises an exception (handled in main) if captions can't be retrieved."""

    # Import here so that a missing library produces a friendly message in main()
    from youtube_transcript_api import YouTubeTranscriptApi

    # ---- Newer versions (1.x): create an instance, then call .fetch() ----
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id)          # returns a FetchedTranscript object
        # Convert each snippet into a plain dictionary so the rest of the
        # script doesn't care which library version we used.
        result = []
        for snippet in fetched:
            result.append({
                "text": snippet.text,
                "start": snippet.start,
                "duration": snippet.duration,
            })
        return result
    except AttributeError:
        # This version doesn't have .fetch() -- fall through to the old API.
        pass

    # ---- Older versions (0.6.x): a single class method that returns dicts ----
    return YouTubeTranscriptApi.get_transcript(video_id)


# =============================================================================
# SECTION 3 -- Format a number of seconds into mm:ss
# =============================================================================

def seconds_to_mmss(seconds):
    """Turn 75.4 seconds into the string '01:15'. Hours roll into minutes
    (e.g. 1h2m would show as 62:00), which keeps it simple and sortable."""
    total = int(seconds)             # drop the fractional part
    minutes = total // 60
    secs = total % 60
    return f"{minutes:02d}:{secs:02d}"   # :02d means "pad to 2 digits with zeros"


# =============================================================================
# SECTION 4 -- Save the transcript to a CSV file
# =============================================================================

def write_csv(video_id, entries):
    """Write a CSV named '<video_id>.csv' with columns timestamp_mm_ss, text.
    Returns the filename so we can tell the user where it went."""
    filename = f"{video_id}.csv"
    # newline="" is the recommended setting so the csv module controls line
    # endings; utf-8 keeps non-English characters intact.
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_mm_ss", "text"])     # the header row
        for entry in entries:
            timestamp = seconds_to_mmss(entry["start"])
            # Collapse any internal newlines so each caption stays on one CSV row.
            text = entry["text"].replace("\n", " ").strip()
            writer.writerow([timestamp, text])
    return filename


# =============================================================================
# SECTION 5 -- The main program: tie everything together
# =============================================================================

def main():
    # ---- 5a. Get the URL: from the command line if given, else by asking ----
    if len(sys.argv) > 1:
        # Everything after the script name, joined, lets unquoted URLs work too.
        url = " ".join(sys.argv[1:]).strip()
    else:
        try:
            url = input("Paste a YouTube URL and press Return: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return 1

    if not url:
        print("ERROR: No URL was provided.")
        return 1

    # ---- 5b. Extract the video ID, or explain that the URL wasn't valid ----
    video_id = extract_video_id(url)
    if not video_id:
        print("ERROR: Could not recognize a YouTube video in that link.")
        print("Supported examples:")
        print("  https://www.youtube.com/watch?v=VIDEOID")
        print("  https://youtu.be/VIDEOID")
        print("  https://www.youtube.com/shorts/VIDEOID")
        return 1

    print(f"Found video ID: {video_id}")
    print("Fetching captions... (this needs an internet connection)\n")

    # ---- 5c. Fetch captions, catching the things that can realistically go wrong ----
    try:
        entries = fetch_transcript(video_id)

    except ImportError:
        # The library itself isn't installed.
        print("ERROR: The 'youtube-transcript-api' library is not installed.")
        print("Run this once in a-Shell, then try again:")
        print("    pip install youtube-transcript-api")
        return 1

    except Exception as e:
        # The library raises many specific error types. Rather than import each
        # one (their names also vary by version), we read the class name as text
        # and give the most helpful message we can.
        error_name = type(e).__name__
        message = str(e)

        # No captions exist / they are turned off / the language isn't there.
        if error_name in (
            "TranscriptsDisabled",
            "NoTranscriptFound",
            "NoTranscriptAvailable",
            "VideoUnavailable",
        ):
            print("ERROR: No captions are available for this video.")
            print("(The uploader may have disabled subtitles, or none exist.)")
            return 1

        # Network problems usually surface as connection/timeout/URL errors.
        lowered = (error_name + " " + message).lower()
        if any(word in lowered for word in
               ("network", "connection", "timed out", "timeout",
                "temporary failure", "getaddrinfo", "urlerror", "ssl")):
            print("ERROR: A network problem stopped the download.")
            print("Check your internet connection and try again.")
            return 1

        # Anything else: show the raw details so the cause is still visible.
        print(f"ERROR: Could not fetch the transcript ({error_name}).")
        print(f"Details: {message}")
        return 1

    # An empty result is rare but possible -- treat it as "no captions".
    if not entries:
        print("ERROR: No caption text was returned for this video.")
        return 1

    # ---- 5d. Save the CSV file ----
    try:
        csv_name = write_csv(video_id, entries)
        print(f"Saved CSV: {csv_name}  ({len(entries)} lines)\n")
    except OSError as e:
        print(f"ERROR: Could not write the CSV file: {e}")
        return 1

    # ---- 5e. Print the clean, copy-pasteable transcript ----
    print("=" * 60)
    print("TRANSCRIPT (select and copy the lines below)")
    print("=" * 60)
    for entry in entries:
        timestamp = seconds_to_mmss(entry["start"])
        text = entry["text"].replace("\n", " ").strip()
        print(f"[{timestamp}] {text}")

    return 0   # 0 means "finished successfully"


# This standard line means: only run main() when the file is executed directly
# (which is exactly what happens when you type `python yt_transcript.py`).
if __name__ == "__main__":
    sys.exit(main())
