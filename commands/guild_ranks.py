from apscheduler.triggers.cron import CronTrigger
import hikari
import aiohttp
import os
import json
import asyncio
from utils import get_config
from datetime import datetime, timezone
from urllib.parse import quote, quote_plus

DEFAULT_RAID_SLUG = "manaforge-omega"
THUMBNAIL_URL = "https://cdn.raiderio.net/images/brand/Icon_2ColorWhite.png"

CONFIG = get_config()
RAIDERIO_TOKEN = os.getenv("RAIDERIO_TOKEN", "").strip()


def setup_guild_rank_tracker(bot):
    @bot.listen(hikari.StartedEvent)
    async def on_started(_: hikari.StartedEvent) -> None:
        await run_guild_rank_check_once(bot)
        schedule_guild_rank_job(bot)


def schedule_guild_rank_job(bot):
    info = CONFIG.get("guild_rank_group", {})
    cron_schedule = info.get("cron_schedule", "*/15 * * * *")
    bot.d.sched.add_job(
        check_all_guild_ranks,
        CronTrigger.from_crontab(cron_schedule),
        args=[bot, info, info.get("raid_slug", DEFAULT_RAID_SLUG)],
        id="guild_rank_check",
        replace_existing=True,
    )
    print(f"Guild rank tracker scheduled with cron: '{cron_schedule}'")


async def run_guild_rank_check_once(bot):
    info = CONFIG.get("guild_rank_group", {})
    await check_all_guild_ranks(bot, info, info.get("raid_slug", DEFAULT_RAID_SLUG))


async def fetch_guild_rank(region, realm, name, raid_slug):
    if not RAIDERIO_TOKEN:
        print("Warning: RAIDERIO_TOKEN not set in environment.")

    region_enc = quote(region)
    realm_enc = quote(realm)
    name_enc = quote_plus(name)

    print(f"Fetching {raid_slug.replace('-', ' ').title()} ranks for {name} in {region}/{realm}...")

    url = (
        f"https://raider.io/api/v1/guilds/profile?"
        f"access_key={RAIDERIO_TOKEN}&"
        f"region={region_enc}&"
        f"realm={realm_enc}&"
        f"name={name_enc}&"
        f"fields=raid_progression,raid_rankings"
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"Failed to fetch data for {name}, status code: {response.status}")
                return None
            data = await response.json()

            raid_prog = data.get('raid_progression', {})
            raid_data = raid_prog.get(raid_slug)
            if not raid_data:
                print(f"No {raid_slug} data for {name}")
                return {
                    "mythic_world_rank": "N/A",
                    "heroic_world_rank": "N/A",
                    "normal_world_rank": "N/A",
                    "summary": "N/A"
                }

            summary = raid_data.get('summary', 'N/A')
            raid_rankings = data.get('raid_rankings', {})
            rank_info = raid_rankings.get(raid_slug, {})

            mythic_rank = rank_info.get('mythic', {})
            heroic_rank = rank_info.get('heroic', {})
            normal_rank = rank_info.get('normal', {})

            return {
                "mythic_world_rank": str(mythic_rank.get('world', 'N/A')),
                "heroic_world_rank": str(heroic_rank.get('world', 'N/A')),
                "normal_world_rank": str(normal_rank.get('world', 'N/A')),
                "summary": summary
            }


async def check_all_guild_ranks(bot, info, raid_slug):
    print("Starting guild ranks check...")
    guilds = info["guilds"]
    ranks_file = info["filename"]
    message_file = info["message_filename"]
    raid_slug = info.get("raid_slug", DEFAULT_RAID_SLUG)

    if os.path.exists(ranks_file):
        with open(ranks_file, "r", encoding="utf-8") as f:
            previous_ranks = json.load(f)
        print(f"Loaded previous ranks from {ranks_file}")
    else:
        previous_ranks = {}
        print("No previous ranks file found, starting fresh")

    updated = False

    def parse_rank(rank_str):
        try:
            rank = int(rank_str)
            return rank if rank > 0 else 999999
        except (ValueError, TypeError):
            return 999999

    semaphore = asyncio.Semaphore(CONFIG.get("concurrency_limit", 5))

    async def fetch_and_parse(g):
        async with semaphore:
            print(f"Checking guild: {g['name']}")
            data = await fetch_guild_rank(g["region"], g["realm"], g["name"], raid_slug)
            if not data:
                return {
                    "name": g['name'],
                    "region": g['region'],
                    "realm": g['realm'],
                    "mythic_rank_str": "N/A",
                    "mythic_rank_int": 999999,
                    "heroic_rank_str": "N/A",
                    "heroic_rank_int": 999999,
                    "normal_rank_str": "N/A",
                    "normal_rank_int": 999999,
                    "summary": "Failed to fetch",
                    "difficulty": 0,  # no kills
                    "progress_score": 0,
                }

            mythic_rank = data.get("mythic_world_rank", "N/A")
            heroic_rank = data.get("heroic_world_rank", "N/A")
            normal_rank = data.get("normal_world_rank", "N/A")
            summary = data.get("summary", "N/A")

            # assign difficulty bucket
            if mythic_rank != "N/A":
                difficulty = 3
            elif heroic_rank != "N/A":
                difficulty = 2
            elif normal_rank != "N/A":
                difficulty = 1
            else:
                difficulty = 0

            # calculate progress score based on summary (e.g., "3/8 M")
            progress_score = 0
            try:
                if summary != "N/A":
                    parts = summary.split()
                    killed_part = parts[0] if len(parts) >= 2 else "0/0"
                    diff_part = parts[-1].upper()
                    killed_num = int(killed_part.split("/")[0])
                    if diff_part == "M":
                        progress_score = 3000 + killed_num
                    elif diff_part == "H":
                        progress_score = 2000 + killed_num
                    elif diff_part == "N":
                        progress_score = 1000 + killed_num
            except Exception:
                progress_score = 0

            key = f"{g['region']}:{g['realm']}:{g['name']}"
            prev_data = previous_ranks.get(key, {})

            nonlocal updated
            if (
                    mythic_rank != prev_data.get("mythic_world_rank")
                    or heroic_rank != prev_data.get("heroic_world_rank")
                    or normal_rank != prev_data.get("normal_world_rank")
                    or summary != prev_data.get("summary")
            ):
                print(
                    f"Update for {g['name']}: "
                    f"Mythic {prev_data.get('mythic_world_rank')} -> {mythic_rank}, "
                    f"Heroic {prev_data.get('heroic_world_rank')} -> {heroic_rank}, "
                    f"Normal {prev_data.get('normal_world_rank')} -> {normal_rank}, "
                    f"Summary {prev_data.get('summary')} -> {summary}"
                )
                previous_ranks[key] = {
                    "mythic_world_rank": mythic_rank,
                    "heroic_world_rank": heroic_rank,
                    "normal_world_rank": normal_rank,
                    "summary": summary,
                }
                updated = True

            return {
                "name": g['name'],
                "region": g['region'],
                "realm": g['realm'],
                "mythic_rank_str": mythic_rank,
                "mythic_rank_int": parse_rank(mythic_rank),
                "heroic_rank_str": heroic_rank,
                "heroic_rank_int": parse_rank(heroic_rank),
                "normal_rank_str": normal_rank,
                "normal_rank_int": parse_rank(normal_rank),
                "summary": summary,
                "difficulty": difficulty,
                "progress_score": progress_score,
            }

    guilds_with_ranks = await asyncio.gather(*[fetch_and_parse(g) for g in guilds])

    if not updated:
        print("No rank or summary updates found.")
        if os.path.exists(message_file):
            print(f"Message file {message_file} exists, skipping message update.")
        return

    with open(ranks_file, "w", encoding="utf-8") as f:
        json.dump(previous_ranks, f, indent=2, ensure_ascii=False)
    print(f"Updated ranks saved to {ranks_file}")

    # Sort: Mythic > Heroic > Normal > None, then by best rank inside that bucket
    def sort_key(g):
        if g["difficulty"] == 3:
            return (0, g["mythic_rank_int"])
        elif g["difficulty"] == 2:
            return (1, g["heroic_rank_int"])
        elif g["difficulty"] == 1:
            return (2, g["normal_rank_int"])
        else:
            return (3, 999999)

    # Sort by progress_score descending, then by best world rank as tiebreaker
    guilds_with_ranks.sort(
        key=lambda g: (
            -g["progress_score"],  # highest progress first
            g["mythic_rank_int"],  # best mythic rank first
            g["heroic_rank_int"],  # best heroic rank next
            g["normal_rank_int"]  # best normal rank last
        )
    )

    now = datetime.now(timezone.utc)
    unix_ts = int(now.timestamp())

    embed = hikari.Embed(
        title=f"Guild World Ranks   -   {raid_slug.replace('-', ' ').title()}",
        color=0x0070FF,
    )
    embed.set_thumbnail(THUMBNAIL_URL)

    max_fields = 24
    count = 0
    for g in guilds_with_ranks:
        if count >= max_fields:
            break

        display_name = g['name']

        # Determine the best available rank to display
        if g['mythic_rank_int'] < 999999:
            best_diff = "Mythic"
            best_rank_str = f"#{g['mythic_rank_str']}"
        elif g['heroic_rank_int'] < 999999:
            best_diff = "Heroic"
            best_rank_str = f"#{g['heroic_rank_str']}"
        elif g['normal_rank_int'] < 999999:
            best_diff = "Normal"
            best_rank_str = f"#{g['normal_rank_str']}"
        else:
            best_diff = "N/A"
            best_rank_str = "N/A"

        summary = g.get("summary", "N/A")
        profile_url = f"https://raider.io/guilds/{g['region'].lower()}/{quote(g['realm'].lower())}/{quote(g['name'])}"

        field_name = f"{display_name}"
        field_value = (
            f"World Rank: {best_diff} {best_rank_str}\n"
            f"Progress: {summary}\n"
            f"[Raider.IO Link]({profile_url})"
        )

        embed.add_field(name=field_name, value=field_value, inline=False)
        count += 1

    embed.add_field(name="Last Update", value=f"<t:{unix_ts}:R>", inline=False)

    channel_keys = info["channel_key"]
    if isinstance(channel_keys, str):
        channel_keys = [channel_keys]

    for ch_key in channel_keys:
        channel_id = CONFIG["channel_ids"].get(ch_key)
        if not channel_id:
            print(f"Channel key '{ch_key}' not found in config channel_ids.")
            continue
        print(f"Sending guild rank update to channel ID: {channel_id}")

        per_channel_message_file = f"{message_file}_{ch_key}"

        try:
            with open(per_channel_message_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
                message_id = saved.get("message_id")
                print(f"Loaded existing message ID for channel '{ch_key}': {message_id}")
        except FileNotFoundError:
            message_id = None
            print(f"No previous message ID found for channel '{ch_key}', sending new message.")

        try:
            if message_id:
                print(f"Editing existing guild rank message for channel '{ch_key}'...")
                await bot.rest.edit_message(channel=channel_id, message=message_id, embed=embed)
            else:
                print(f"Creating new guild rank message for channel '{ch_key}'...")
                msg = await bot.rest.create_message(channel_id, embed)
                with open(per_channel_message_file, "w", encoding="utf-8") as f:
                    json.dump({"message_id": msg.id}, f)
                print(f"Saved new message ID for channel '{ch_key}': {msg.id}")
        except Exception as e:
            print(f"Failed to send/edit guild rank message for channel '{ch_key}': {e}")

    print("Guild ranks check complete.")
