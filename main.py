
import asyncio
import logging
import os

from aiohttp import ClientSession
from json import loads
from json.decoder import JSONDecodeError
from pyrogram import Client
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

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


async def nme(client: Client, message: Message):
    if (
        message and
        message.from_user and
        message.from_user.is_bot
    ):
        usernameEntity = message.from_user
        username = usernameEntity.username
        if username:
            username = username.lower()
        replied = message.reply_to_message
        if not replied:
            replied = message
        ping_time = round(
            message.date.timestamp() - replied.date.timestamp(),
            2
        )
        # ? no friendly method to mark read
        return await update_data(
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
        client = Client(
            "bot-status-api-updater",
            session_string=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            sleep_threshold=TG_FLOOD_SLEEP_THRESHOLD,
            device_model=TG_DEVICE_MODEL,
            system_version=TG_SYSTEM_VERSION,
            app_version=TG_APP_VERSION,
        )
        # register event handler to check bot responses
        client.add_handler(
            MessageHandler(
                nme,
                filters.incoming
            )
        )
        # start the userbot
        await client.start()
        cache = client.me
        # send /start to all the bots
        reqs = []
        for bot in bots:
            reqs.append(
                client.send_message(
                    bot["username"],
                    bot["start_param"],
                )
            )
        await asyncio.gather(*reqs)
        await asyncio.sleep(DELAY_TIMEOUT)
        await client.stop()      
    # finally, do this
    txtContent = await ootu()
    with open("index.html", "w+") as fod:
        fod.write(txtContent)


if __name__ == "__main__":
    asyncio.run(main())
