# Add Season Script
# Modified from original setupbot.py by Pigeonburger
# https://github.com/pigeonburger

import os, re, glob, sqlite3 as db

# This is the frame-splitting part (this will probably take a while depending on how fast your computer is)

# Get all the mkv files in the current folder (change file extension if needed)
eps = glob.glob("*.mkv")

# Number of frames per second you want the show to be split into
fps = 1

# Create frames directory if it doesn't exist
if not os.path.exists('frames'):
    os.mkdir('frames')

# Supports common file season-episode formats e.g. S01E01, 01x01, Season 1 Episode 1 etc.
regx = re.compile(r"(?:.*)(?:s|season|)\s?(\d{1,2})\s?(?:e|x|episode|ep|\n)\s?(\d{1,2})", re.IGNORECASE)

# Process each episode file
for ep in eps:
    ep_regx = regx.match(ep)

    if ep_regx:
        # Parse to get the video's season and episode numbers
        season, episode = ep_regx.groups()

        # All videos will be stored in a folder called 'frames', inside another folder denoting the season number
        out_path = f'./frames/S{season.zfill(2)}'
        if not os.path.isdir(out_path):
            os.mkdir(out_path)

        # The outputted frame files will look like 00x00.jpg, where the number on the left side of the x is the episode number, and the number on the right side is the frame number.
        # Using high quality settings, maintaining aspect ratio, and burning in English subtitles
        os.system(f'ffmpeg -i "{ep}" -vf "subtitles=\'{ep}\':force_style=\'FontSize=14\',fps={fps}" -q:v 1 {out_path}/{episode}x%d.jpg')

print("✓ Finished extracting frames")

# Connect to existing database or create if it doesn't exist
connection = db.connect("framebot.db")
cursor = connection.cursor()

# Create tables if they don't exist (won't affect existing tables)
cursor.execute("""CREATE TABLE IF NOT EXISTS show (ep, frames)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS bot (current_episode, last_frame)""")

# Initialize bot table if empty
bot_data = cursor.execute("SELECT * FROM bot").fetchone()
if not bot_data:
    cursor.execute('INSERT INTO bot(current_episode, last_frame) VALUES ("01x01", 0)')
    connection.commit()

# Get the season number from processed files
if not eps:
    print("No episode files found! Please put your .mkv files in this directory.")
    exit(1)

total_seasons = max(int(regx.match(ep).groups()[0]) for ep in eps if regx.match(ep))
print(f"Found files for season {total_seasons}")

# Store the number of frames per episode in database
current_season = str(total_seasons).zfill(2)
total_eps = len(glob.glob(f"./frames/S{current_season}/*x1.jpg"))

if total_eps == 0:
    print(f"No frames found for season {total_seasons}! Something went wrong with frame extraction.")
    exit(1)

print(f"Adding {total_eps} episodes to database...")

# Remove any existing entries for this season to avoid duplicates
cursor.execute(f'DELETE FROM show WHERE ep LIKE "{current_season}x%"')

# Add new entries for this season
for i in range(total_eps):
    current_ep = str(i + 1).zfill(2)
    frames = glob.glob(f"./frames/S{current_season}/{current_ep}x*.jpg")
    cursor.execute(f'INSERT INTO show (ep, frames) VALUES ("{current_season}x{current_ep}", {len(frames)})')
    print(f"Added S{current_season}E{current_ep} with {len(frames)} frames")
        
connection.commit()
connection.close()

print("\nDone! The new season has been added to the database.")
print("You can now continue running bot.py as normal.")
