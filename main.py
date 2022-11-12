
from aiohttp import ClientSession
from time import time
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.events import NewMessage
from telethon.tl.functions.messages import SendMessageRequest
import asyncio
import os
import logging
from json import loads
from json.decoder import JSONDecodeError

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
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


API_ID = int(get_config("API_ID", should_prompt=True))
API_HASH = get_config("API_HASH", should_prompt=True)
SESSION = get_config("SESSION", should_prompt=True)
ENDPOINT_API_KEY = get_config("ENDPOINT_API_KEY", "thisismysecret")
GET_ENDPOINT = get_config("GET_ENDPOINT", "http://example.com/getallbots")
UPDATE_ENDPOINT = get_config("UPDATE_ENDPOINT", "http://example.com/updatebotstatus")
OOTU_ENDPOINT = get_config("OOTU_ENDPOINT", "http://example.com/ootumightwork")
CHECK_TIMEOUT = int(get_config("CHECK_TIMEOUT", "25"))
DELAY_TIMEOUT = int(get_config("DELAY_TIMEOUT", "5"))
TG_FLOOD_SLEEP_THRESHOLD = int(get_config("TG_FLOOD_SLEEP_THRESHOLD", "60"))
TG_DEVICE_MODEL = get_config("TG_DEVICE_MODEL")
TG_SYSTEM_VERSION = get_config("TG_SYSTEM_VERSION")
TG_APP_VERSION = get_config("TG_APP_VERSION")
CUST_HEADERS = {
    "x-api-key": ENDPOINT_API_KEY
}


async def get_bots():
    async with ClientSession() as session:
        one = await session.post(
            GET_ENDPOINT,
            headers=CUST_HEADERS
        )
        owt = await one.text()
        try:
            return loads(owt)
        except JSONDecodeError:
            return []


async def update_data(username, ping_time):
    update_param_s = {
        "username": username,
        "ping_time": ping_time,
        "online_status": 1,
    }
    # logger.info(update_param_s)
    async with ClientSession() as session:
        one = await session.post(
            UPDATE_ENDPOINT,
            json=update_param_s,
            headers=CUST_HEADERS
        )
        return await one.text()


async def ootu():
    async with ClientSession() as session:
        one = await session.post(
            OOTU_ENDPOINT,
            headers=CUST_HEADERS
        )
        return await one.text()


async def nme(evt: NewMessage.Event):
    # logger.info("updating database")
    username = (await evt.client.get_entity(
        evt.sender_id
    )).username
    if username:
        username = username.lower()
    replied = await evt.get_reply_message()
    if not replied:
        replied = evt
    ping_time = round(
        evt.date.timestamp() - replied.date.timestamp(),
        2
    )
    await update_data(
        username,
        ping_time
    )


async def main():
    # get the list of bots
    bots = await get_bots()
    logger.info(
        f"Found {len(bots)} Bots"
    )
    if len(bots) > 0:
        # log in as user account,
        client = TelegramClient(
            StringSession(SESSION),
            API_ID,
            API_HASH,
            flood_sleep_threshold=TG_FLOOD_SLEEP_THRESHOLD,
            device_model=TG_DEVICE_MODEL,
            system_version=TG_SYSTEM_VERSION,
            app_version=TG_APP_VERSION,
        )
        # register event handler to check bot responses
        client.add_event_handler(nme, NewMessage(
            incoming=True
        ))
        # start the userbot
        await client.start()
        cache = await client.get_me()
        # send /start to all the bots
        reqs = []
        for bot in bots:
            if len(reqs) > 10:
                await client(reqs)
                reqs = []
                await asyncio.sleep(CHECK_TIMEOUT)
            reqs.append(
                SendMessageRequest(
                    peer=bot["username"],
                    message=bot["start_param"],
                )
            )
        if len(reqs) > 0:
            await client(reqs)
            reqs = []
        await asyncio.sleep(DELAY_TIMEOUT)
        await client.disconnect()      
    # finally, do this
    await ootu()


if __name__ == "__main__":
    asyncio.run(main())
