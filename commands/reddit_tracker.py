import os
import hikari
import asyncpraw
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from utils import get_config, hex_to_int

load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "YOUR_REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "YOUR_REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv(
    "REDDIT_USER_AGENT",
    "script:reddit_to_discord:v1.0 (by /u/YOUR_USERNAME)"
)

reddit = None  # Will hold asyncpraw.Reddit instance


def setup_reddit():
    global reddit
    reddit = asyncpraw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )


def setup_reddit_tracker(bot):
    @bot.listen(hikari.StartedEvent)
    async def on_started(event: hikari.StartedEvent) -> None:
        # Initialize Reddit instance synchronously before first use
        setup_reddit()

        # Run your initial checks and setup scheduled jobs
        await run_initial_check(bot)
        await initialize_reddit_checks(bot)


async def initialize_reddit_checks(bot):
    config = get_config()
    reddit_sources = config.get("reddit_sources", {})
    channel_ids = config.get("channel_ids", {})

    for name, source in reddit_sources.items():
        username = source["username"]
        color_int = hex_to_int(source.get("color", "#ffffff"))
        filename = source.get("filename", f"reddit/{username}.txt")
        channels = [channel_ids[ch] for ch in source["channels"]]

        cron_schedule = source.get("cron_schedule", "*/5")  # default every 5 minutes

        bot.d.sched.add_job(
            check_and_announce_reddit,
            CronTrigger.from_crontab(cron_schedule),
            args=[bot, username, filename, color_int, channels],
            misfire_grace_time=None,
            replace_existing=True,
            id=f"reddit_{username}"
        )


async def run_initial_check(bot):
    config = get_config()
    reddit_sources = config.get("reddit_sources", {})
    channel_ids = config.get("channel_ids", {})

    for name, source in reddit_sources.items():
        username = source["username"]
        color_int = hex_to_int(source.get("color", "#ffffff"))
        filename = source.get("filename", f"reddit/{username}.txt")
        channels = [channel_ids[ch] for ch in source["channels"]]

        await check_and_announce_reddit(bot, username, filename, color_int, channels)


async def check_and_announce_reddit(bot, username, base_filename, color, channels):
    # 1) Submissions
    new_submissions = await fetch_all_submissions(username)
    if new_submissions:
        await announce_submissions(bot, username, base_filename, color, channels, new_submissions)
    else:
        print(f"[Reddit] No submissions found for u/{username}.")

    # 2) Comments
    new_comments = await fetch_all_comments(username)
    if new_comments:
        comments_filename = base_filename.replace(".txt", "_comments.txt")
        await announce_comments(bot, username, comments_filename, color, channels, new_comments)
    else:
        print(f"[Reddit] No comments found for u/{username}.")


async def fetch_all_submissions(username: str):
    results = []
    try:
        redditor = await reddit.redditor(username)  # Await here!
        async for submission in redditor.submissions.new(limit=None):
            results.append(submission)
    except Exception as ex:
        print(f"[Error] while fetching submissions for {username}: {ex}")
    return results


async def fetch_all_comments(username: str):
    results = []
    try:
        redditor = await reddit.redditor(username)  # Await here!
        async for comment in redditor.comments.new(limit=None):
            results.append(comment)
    except Exception as ex:
        print(f"[Error] while fetching comments for {username}: {ex}")
    return results


async def announce_submissions(bot, username, filename, color, channels, submissions):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    seen_ids = set()
    if os.path.exists(filename):
        with open(filename, "r") as f:
            seen_ids = set(line.strip() for line in f)

    unannounced = [s for s in submissions if s.id not in seen_ids]

    if not unannounced:
        print(f"[Reddit] All submissions by u/{username} already announced.")
        return

    unannounced.sort(key=lambda s: s.created_utc)
    print(f"[Reddit] Found {len(unannounced)} new submissions by u/{username}.")

    for submission in unannounced:
        embed = create_submission_embed(submission, color)
        for cid in channels:
            await bot.rest.create_message(cid, embed=embed)
        seen_ids.add(submission.id)

    with open(filename, "w") as f:
        f.write("\n".join(seen_ids))

    print(f"[Reddit] Announced {len(unannounced)} new submissions for u/{username}.")


async def announce_comments(bot, username, filename, color, channels, comments):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    seen_ids = set()
    if os.path.exists(filename):
        with open(filename, "r") as f:
            seen_ids = set(line.strip() for line in f)

    unannounced = [c for c in comments if c.id not in seen_ids]

    if not unannounced:
        print(f"[Reddit] All comments by u/{username} already announced.")
        return

    unannounced.sort(key=lambda c: c.created_utc)
    print(f"[Reddit] Found {len(unannounced)} new comments by u/{username}.")

    for comment in unannounced:
        embed = create_comment_embed(comment, color)
        for cid in channels:
            await bot.rest.create_message(cid, embed=embed)
        seen_ids.add(comment.id)

    with open(filename, "w") as f:
        f.write("\n".join(seen_ids))

    print(f"[Reddit] Announced {len(unannounced)} new comments for u/{username}.")


def create_submission_embed(submission, color):
    created_ts = int(submission.created_utc)
    relative_time = f"<t:{created_ts}:R>"

    embed = hikari.Embed(
        title=f"New post by u/{submission.author}",
        description=submission.title,
        color=color
    )
    embed.add_field("Submission URL", submission.url, inline=False)
    embed.add_field("Reddit Link", f"https://reddit.com{submission.permalink}", inline=False)
    embed.add_field("Posted", relative_time, inline=False)
    return embed


def create_comment_embed(comment, color):
    created_ts = int(comment.created_utc)
    relative_time = f"<t:{created_ts}:R>"

    embed = hikari.Embed(
        title=f"New comment by u/{comment.author}",
        description=(comment.body[:1024] if comment.body else "No body"),
        color=color
    )
    embed.add_field("Subreddit", str(comment.subreddit), inline=False)
    embed.add_field("Comment Link", f"https://reddit.com{comment.permalink}", inline=False)
    embed.add_field("Posted", relative_time, inline=False)
    return embed
