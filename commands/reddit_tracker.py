import os
import hikari
import lightbulb
import asyncpraw
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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

reddit = None

loader = lightbulb.Loader()


def setup_reddit():
    global reddit
    reddit = asyncpraw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )


@loader.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent, bot: hikari.GatewayBot, sched: AsyncIOScheduler) -> None:
    setup_reddit()
    await run_initial_check(bot)
    await initialize_reddit_checks(bot, sched)


@loader.listener(hikari.StoppingEvent)
async def on_stopping(event: hikari.StoppingEvent) -> None:
    if reddit is not None:
        await reddit.close()


async def initialize_reddit_checks(bot: hikari.GatewayBot, sched: AsyncIOScheduler):
    config = get_config()
    reddit_sources = config.get("reddit_sources", {})
    channel_ids = config.get("channel_ids", {})

    for name, source in reddit_sources.items():
        username = source["username"]
        color_int = hex_to_int(source.get("color", "#ffffff"))
        filename = source.get("filename", f"reddit/{username}.txt")
        channels = [channel_ids[ch] for ch in source["channels"]]
        cron_schedule = source.get("cron_schedule", "*/5 * * * *")

        sched.add_job(
            check_and_announce_reddit,
            CronTrigger.from_crontab(cron_schedule),
            args=[bot, username, filename, color_int, channels],
            misfire_grace_time=None,
            replace_existing=True,
            id=f"reddit_{username}"
        )


async def run_initial_check(bot: hikari.GatewayBot):
    config = get_config()
    reddit_sources = config.get("reddit_sources", {})
    channel_ids = config.get("channel_ids", {})

    for name, source in reddit_sources.items():
        username = source["username"]
        color_int = hex_to_int(source.get("color", "#ffffff"))
        filename = source.get("filename", f"reddit/{username}.txt")
        channels = [channel_ids[ch] for ch in source["channels"]]
        await check_and_announce_reddit(bot, username, filename, color_int, channels)


# How many recent items to fetch per check. New items always appear at the top
# of the listing, so a small window is enough and keeps API usage low.
FETCH_LIMIT = 25


async def check_and_announce_reddit(bot, username, base_filename, color, channels):
    submissions = await fetch_recent(username, "submissions")
    if submissions is not None:
        await announce_new(bot, "submission", username, base_filename, channels, submissions,
                           lambda s: create_submission_embed(s, color))

    comments = await fetch_recent(username, "comments")
    if comments is not None:
        comments_filename = base_filename.replace(".txt", "_comments.txt")
        await announce_new(bot, "comment", username, comments_filename, channels, comments,
                           lambda c: create_comment_embed(c, color))


async def fetch_recent(username: str, listing: str):
    """Return the newest items from a redditor's submissions/comments, or None on error."""
    results = []
    try:
        redditor = await reddit.redditor(username)
        async for item in getattr(redditor, listing).new(limit=FETCH_LIMIT):
            results.append(item)
    except Exception as ex:
        print(f"[Reddit] Error while fetching {listing} for u/{username}: {type(ex).__name__}: {ex}")
        return None
    return results


async def send_to_channels(bot, channels, embed):
    for cid in channels:
        try:
            await bot.rest.create_message(cid, embed=embed)
        except Exception as ex:
            print(f"[Reddit] Failed to send to channel {cid}: {type(ex).__name__}: {ex}")


async def announce_new(bot, kind, username, filename, channels, items, make_embed):
    if os.path.dirname(filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)

    if not os.path.exists(filename):
        # First run for this source: record what already exists instead of
        # flooding the channels with the user's whole history.
        with open(filename, "w") as f:
            f.write("\n".join(i.id for i in items))
        print(f"[Reddit] Seeded {len(items)} existing {kind}s for u/{username}, nothing announced.")
        return

    with open(filename, "r") as f:
        seen_ids = set(line.strip() for line in f if line.strip())

    unannounced = sorted((i for i in items if i.id not in seen_ids), key=lambda i: i.created_utc)
    if not unannounced:
        print(f"[Reddit] No new {kind}s for u/{username}.")
        return

    print(f"[Reddit] Found {len(unannounced)} new {kind}s by u/{username}.")
    try:
        for item in unannounced:
            await send_to_channels(bot, channels, make_embed(item))
            seen_ids.add(item.id)
    finally:
        with open(filename, "w") as f:
            f.write("\n".join(seen_ids))


def create_submission_embed(submission, color):
    created_ts = int(submission.created_utc)
    embed = hikari.Embed(
        title=f"New post by u/{submission.author}",
        description=submission.title,
        color=color
    )
    embed.add_field("Submission URL", submission.url, inline=False)
    embed.add_field("Reddit Link", f"https://reddit.com{submission.permalink}", inline=False)
    embed.add_field("Posted", f"<t:{created_ts}:R>", inline=False)
    return embed


def create_comment_embed(comment, color):
    created_ts = int(comment.created_utc)
    embed = hikari.Embed(
        title=f"New comment by u/{comment.author}",
        description=(comment.body[:1024] if comment.body else "No body"),
        color=color
    )
    embed.add_field("Subreddit", str(comment.subreddit), inline=False)
    embed.add_field("Comment Link", f"https://reddit.com{comment.permalink}", inline=False)
    embed.add_field("Posted", f"<t:{created_ts}:R>", inline=False)
    return embed
