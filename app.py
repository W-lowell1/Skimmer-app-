# =============================================================================
# YouTube Transcript Extractor -- Web App (Streamlit)
# =============================================================================
#
# This is the "app on your phone" version. It is a small web app you open in
# Safari and then "Add to Home Screen" so it gets its own icon and opens like
# a normal app -- no App Store, no Mac, no jailbreak needed.
#
# It reuses the exact same transcript logic from yt_transcript.py, so both the
# command-line script and this web app behave identically.
#
# HOW TO RUN IT LOCALLY (optional, on a computer):
#     pip install -r requirements.txt
#     streamlit run app.py
#
# HOW TO PUT IT ON YOUR PHONE:  see README.md in this repository.
# =============================================================================

import io       # lets us build the CSV file in memory (no saving to disk needed)
import csv      # same CSV writer used by the command-line version
import os       # lets us pass a proxy setting down to the fetch logic
import streamlit as st

# Reuse the building blocks we already wrote and tested in yt_transcript.py.
from yt_transcript import (
    extract_video_id,
    fetch_transcript,
    seconds_to_mmss,
    build_plain_text,
    build_markdown,
)

# --- Optional proxy: pick it up from Streamlit "secrets" if you set one there.
# This is completely optional. If you never set YT_PROXY, the app works normally
# with a direct connection. See README for how/why you might add a proxy.
try:
    if "YT_PROXY" in st.secrets:
        os.environ["YT_PROXY"] = str(st.secrets["YT_PROXY"])
except Exception:
    # No secrets file configured -- that's fine, just means no proxy.
    pass


# -----------------------------------------------------------------------------
# Page setup -- title, icon, and a mobile-friendly layout.
# The page_icon below becomes the little icon Safari uses for the tab/bookmark.
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="YouTube Transcript",
    page_icon="📝",
    layout="centered",          # narrow column reads well on a phone screen
)

st.title("📝 YouTube Transcript")
st.caption("Paste a YouTube link to get the transcript as copyable text and a CSV.")


# -----------------------------------------------------------------------------
# Helper: build the CSV text in memory so we can offer it as a download button.
# (The phone app doesn't save files to a folder the way the a-Shell script does;
#  instead it gives you a Download button, which iOS handles via Files/Share.)
# -----------------------------------------------------------------------------
def build_csv_text(entries):
    """Return the CSV contents as a single string (columns: timestamp_mm_ss, text)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["timestamp_mm_ss", "text"])
    for entry in entries:
        timestamp = seconds_to_mmss(entry["start"])
        text = entry["text"].replace("\n", " ").strip()
        writer.writerow([timestamp, text])
    return buffer.getvalue()


# (The plain-text and Markdown builders live in yt_transcript.py and are
#  imported above, so the app and the command-line tool stay perfectly in sync.)


# -----------------------------------------------------------------------------
# The input box. The button runs the whole process when tapped.
# -----------------------------------------------------------------------------
url = st.text_input(
    "YouTube URL",
    placeholder="https://youtu.be/dQw4w9WgXcQ",
)

# Optional, collapsed by default: a place to paste a proxy URL if YouTube ever
# blocks the server. Most people will never open this. Leaving it blank uses a
# normal direct connection (or whatever YT_PROXY secret you may have set).
with st.expander("Advanced: use a proxy (optional)"):
    st.caption(
        "Only needed if you see a 'temporarily blocked' message. Paste a proxy "
        "URL like http://user:pass@host:port . Leave blank for a normal "
        "connection. Note: proxies that reliably bypass YouTube are usually paid "
        "residential ones — free public proxies rarely work."
    )
    proxy_input = st.text_input(
        "Proxy URL",
        value=os.environ.get("YT_PROXY", ""),
        placeholder="http://user:pass@host:port",
    )

go = st.button("Get transcript", type="primary", use_container_width=True)


# -----------------------------------------------------------------------------
# Main logic -- runs only after the button is tapped (and a URL was entered).
# -----------------------------------------------------------------------------
if go:
    if not url.strip():
        st.warning("Please paste a YouTube URL first.")
        st.stop()

    # 1) Turn the URL into a video ID, or explain that it wasn't recognized.
    video_id = extract_video_id(url)
    if not video_id:
        st.error(
            "Could not recognize a YouTube video in that link.\n\n"
            "Try a link like:\n"
            "- https://www.youtube.com/watch?v=VIDEOID\n"
            "- https://youtu.be/VIDEOID\n"
            "- https://www.youtube.com/shorts/VIDEOID"
        )
        st.stop()

    # 2) Fetch the captions, showing a spinner while it works.
    #    A proxy typed into the Advanced box (if any) takes priority; otherwise
    #    fetch_transcript falls back to the YT_PROXY env var / secret, or none.
    proxy_url = (proxy_input or "").strip() or None
    try:
        with st.spinner("Fetching captions…"):
            entries = fetch_transcript(video_id, proxy_url=proxy_url)
    except Exception as e:
        # Same friendly error categories as the command-line version.
        error_name = type(e).__name__
        message = str(e)
        lowered = (error_name + " " + message).lower()

        if error_name in (
            "TranscriptsDisabled", "NoTranscriptFound",
            "NoTranscriptAvailable", "VideoUnavailable",
        ):
            st.error("No captions are available for this video "
                     "(subtitles may be disabled, or none exist).")
        elif error_name in ("RequestBlocked", "IpBlocked") or "block" in lowered:
            # This is the common one when hosted on a shared cloud server.
            st.error(
                "YouTube temporarily blocked this server's requests. "
                "This can happen on free hosting. Try again in a bit, or run "
                "the command-line version from your own connection."
            )
        elif any(word in lowered for word in
                 ("network", "connection", "timed out", "timeout",
                  "temporary failure", "getaddrinfo", "urlerror", "ssl")):
            st.error("A network problem stopped the download. "
                     "Check the connection and try again.")
        else:
            st.error(f"Could not fetch the transcript ({error_name}).\n\n{message}")
        st.stop()

    # An empty result is rare but possible -- treat it as "no captions".
    if not entries:
        st.error("No caption text was returned for this video.")
        st.stop()

    # 3) Success! Build every output format.
    csv_text = build_csv_text(entries)
    plain_text = build_plain_text(entries)
    markdown_text = build_markdown(video_id, entries, source_url=url)

    st.success(f"Got {len(entries)} caption lines for video {video_id}.")

    # Three download buttons. Markdown is first because it's the best one to
    # drop straight into a project's context folder (it keeps the source link).
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "⬇️ Markdown",
            data=markdown_text,
            file_name=f"{video_id}.md",
            mime="text/markdown",
            use_container_width=True,
            help="Best for context folders — includes the source link.",
        )
    with col2:
        st.download_button(
            "⬇️ CSV",
            data=csv_text,
            file_name=f"{video_id}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            "⬇️ Text",
            data=plain_text,
            file_name=f"{video_id}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # 4) One-tap copy. st.code() shows a copy icon in its top-right corner that
    #    copies the WHOLE block in a single tap -- the easiest way to grab it on
    #    a phone and paste it into a note or context file.
    st.markdown("**Transcript** — tap the copy icon (top-right of the box) to copy it all:")
    st.code(plain_text, language=None)
