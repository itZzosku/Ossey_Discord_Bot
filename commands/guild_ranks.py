from apscheduler.triggers.cron import CronTrigger
import hikari
import aiohttp
import os
import json
import asyncio
from utils import get_config
from datetime import datetime, timezone
from urllib.parse import quote, quote_plus

DEFAULT_RAID_SLUG = "liberation-of-undermine"


def setup_guild_rank_tracker(bot):
    @bot.listen(hikari.StartedEvent)
    async def on_started(_: hikari.StartedEvent) -> None:
        await run_guild_rank_check_once(bot)
        schedule_guild_rank_job(bot)


def schedule_guild_rank_job(bot):
    config = get_config()
    info = config.get("guild_rank_group", {})

    cron_schedule = info.get("cron_schedule", "*/15 * * * *")  # Every 15 minutes by default
    bot.d.sched.add_job(
        check_all_guild_ranks,
        CronTrigger.from_crontab(cron_schedule),
        args=[bot, info, info.get("raid_slug", DEFAULT_RAID_SLUG)],
        id="guild_rank_check",
        replace_existing=True,
    )
    print(f"Guild rank tracker scheduled with cron: '{cron_schedule}'")


async def run_guild_rank_check_once(bot):
    config = get_config()
    info = config.get("guild_rank_group", {})
    await check_all_guild_ranks(bot, info, info.get("raid_slug", DEFAULT_RAID_SLUG))


async def fetch_guild_rank(region, realm, name, raid_slug):
    token = os.getenv("RAIDERIO_TOKEN")
    if not token:
        print("Warning: RAIDERIO_TOKEN not set in environment.")

    region_enc = quote(region.lower())
    realm_enc = quote(realm.lower())
    name_enc = quote_plus(name)  # encode name correctly ONCE

    print(f"Fetching {raid_slug.replace('-', ' ').title()} rank for {name} in {region}/{realm}...")
    print(f"Fetching URL: https://raider.io/api/v1/guilds/profile?access_key={token}&region={region_enc}&realm={realm_enc}&name={name_enc}&fields=raid_progression,raid_rankings")

    url = (
        f"https://raider.io/api/v1/guilds/profile?"
        f"access_key={token}&"
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
                return {"world_rank": "N/A", "summary": "N/A"}

            summary = raid_data.get('summary', 'N/A')

            raid_rankings = data.get('raid_rankings', {})
            rank_info = raid_rankings.get(raid_slug, {})
            mythic_rank = rank_info.get('mythic', {})
            world_rank = mythic_rank.get('world', 'N/A')

            return {"world_rank": str(world_rank) if world_rank != "N/A" else "N/A", "summary": summary}


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
            if rank <= 0:
                return 999999
            return rank
        except (ValueError, TypeError):
            return 999999

    guilds_with_ranks = []
    for g in guilds:
        print(f"Checking guild: {g['name']}")
        data = await fetch_guild_rank(g["region"], g["realm"], g["name"], raid_slug)
        if not data:
            guilds_with_ranks.append({
                "name": g['name'],
                "region": g['region'],
                "realm": g['realm'],
                "rank_str": "N/A",
                "rank_int": 999999,
                "summary": "Failed to fetch"
            })
            continue

        rank = data.get("world_rank", "N/A")
        summary = data.get("summary", "N/A")

        key = f"{g['region']}:{g['realm']}:{g['name']}"
        previous_data = previous_ranks.get(key, {})
        prev_rank = previous_data.get("world_rank", "N/A")
        prev_summary = previous_data.get("summary", "N/A")

        if rank != prev_rank or summary != prev_summary:
            print(f"Update for {g['name']}: {prev_rank} -> {rank} or {prev_summary} -> {summary}")
            previous_ranks[key] = {"world_rank": rank, "summary": summary}
            updated = True

        guilds_with_ranks.append({
            "name": g['name'],
            "region": g['region'],
            "realm": g['realm'],
            "rank_str": rank,
            "rank_int": parse_rank(rank),
            "summary": summary,
        })

        await asyncio.sleep(0.3)

    if not updated:
        print("No rank or summary updates found.")
        if os.path.exists(message_file):
            print(f"Message file {message_file} exists, skipping message update.")
        return

    with open(ranks_file, "w", encoding="utf-8") as f:
        json.dump(previous_ranks, f, indent=2, ensure_ascii=False)
    print(f"Updated ranks saved to {ranks_file}")

    guilds_with_ranks.sort(key=lambda x: x['rank_int'])

    now = datetime.now(timezone.utc)
    unix_ts = int(now.timestamp())

    embed = hikari.Embed(
        title=f"Guild World Ranks - {raid_slug.replace('-', ' ').title()}",
        color=0x0070FF,
    )

    max_fields = 24
    count = 0
    for g in guilds_with_ranks:
        if count >= max_fields:
            break

        display_name = g['name']

        rank_str = f"#{g['rank_str']}" if g['rank_str'] != "N/A" else "N/A"
        summary = g.get("summary", "N/A")
        profile_url = f"https://raider.io/guilds/{g['region'].lower()}/{quote(g['realm'].lower())}/{quote(g['name'])}"

        field_name = f"{display_name}   -    World Rank {rank_str}"
        field_value = f"Progress: {summary}   -   [Profile Link]({profile_url})"

        embed.add_field(name=field_name, value=field_value, inline=False)
        count += 1

    embed.add_field(name="Last Update", value=f"<t:{unix_ts}:R>", inline=False)

    config = get_config()
    channel_keys = info["channel_key"]
    if isinstance(channel_keys, str):
        channel_keys = [channel_keys]

    for ch_key in channel_keys:
        channel_id = config["channel_ids"].get(ch_key)
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
