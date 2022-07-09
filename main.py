from aiohttp import ClientSession
from time import time
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import os
import logging

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("telethon").setLevel(logging.WARNING)  # idc
logger = logging.getLogger(__name__)


def get_config(name: str, d_v=None, should_prompt=False):
    """ wrapper for getting the credentials """
    """ accepts one mandatory variable
    and prompts for the value, if not available """
    val = os.environ.get(name, d_v)
    if not val and should_prompt:
        try:
            val = input(f"enter {name}'s value: ")
        except EOFError:
            val = d_v
        print("\n")
    return val


API_ID = int(get_config("API_ID", "6"))
API_HASH = get_config("API_HASH")
SESSION = get_config("SESSION")
ENDPOINT_API_KEY = get_config("ENDPOINT_API_KEY")
GET_ENDPOINT = get_config("GET_ENDPOINT")
UPDATE_ENDPOINT = get_config("UPDATE_ENDPOINT")
OOTU_ENDPOINT = get_config("OOTU_ENDPOINT")
CHECK_TIMEOUT = 20
DELAY_TIMEOUT = 5
CUST_HEADERS = {
    "x-api-key": ENDPOINT_API_KEY
}


async def get_bots():
    async with ClientSession() as session:
        one = await session.post(
            GET_ENDPOINT,
            headers=CUST_HEADERS
        )
        return await one.json()


async def update_data(username, ping_time, online_status):
    update_param_s = {
        "username": username,
        "ping_time": ping_time,
        "online_status": 1 if online_status else 0
    }
    # logger.info(update_param_s)
    async with ClientSession() as session:
        one = await session.post(
            UPDATE_ENDPOINT,
            json=update_param_s,
            headers=CUST_HEADERS
        )
        owt = await one.json()
        # logger.info(owt)
        return owt


async def ootu():
    async with ClientSession() as session:
        one = await session.post(
            OOTU_ENDPOINT,
            headers=CUST_HEADERS
        )
        return await one.json()


async def main():
    bots = await get_bots()
    # log in as user account,
    # and send /start to all the bots
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    async with client as user:
        for bot in bots:
            bot_username = bot["username"]
            ping_time = 421
            online_status = False
            async with user.conversation(bot_username, exclusive=False) as conv:
                if not bot["can_set_sticker_set"]:
                    bot_username = "[XxXxX]"
                logger.info(f"pinging {bot_username}")
                try:
                    await conv.send_message("/start")
                    s_tart = time()
                    reply = await conv.get_response(timeout=CHECK_TIMEOUT)
                    e_nd_ie = time()
                    ping_time = round(e_nd_ie - s_tart, 2)
                    await reply.mark_read()
                except asyncio.TimeoutError:
                    logger.warning(
                        f"no response from {bot_username} even after {CHECK_TIMEOUT} seconds"
                    )
                else:
                    online_status = True
                    logger.info(f"{bot_username} responded in {ping_time} ms")
                finally:
                    logger.info("updating database")
                    await update_data(bot["username"], ping_time, online_status)
            await asyncio.sleep(DELAY_TIMEOUT)
    # finally, do this
    await ootu()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
