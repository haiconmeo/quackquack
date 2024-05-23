API_ID='25544317'
API_HASH='b061e73d3a7eb3148b1fedf21ce484ff'
import asyncio
from pyrogram import Client
import requests
from bot.config import settings
from bot.utils import logger
from bot.exceptions import InvalidSession
import asyncio
from time import sleep
from time import time
from datetime import datetime
from urllib.parse import unquote
import json
import aiohttp
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered
from pyrogram.raw.functions.messages import RequestWebView
from urllib import parse
from bot.config import settings
from bot.utils import logger
from bot.exceptions import InvalidSession
async def register_sessions() -> None:


    if not API_ID or not API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    session_name = input('\nEnter the session name (press Enter to exit): ')

    if not session_name:
        return None

    session = Client(
        name=session_name,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir="sessions/"
    )

    async with session:
        user_data = await session.get_me()

    logger.success(f'Session added successfully @{user_data.username} | {user_data.first_name} {user_data.last_name}')


async def get_tg_clients() -> list[Client]:
    session_names = ['manh']

    if not session_names:
        raise FileNotFoundError("Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [Client(
        name=session_name,
        api_id=settings.API_ID,
        api_hash=settings.API_HASH,
        workdir='sessions/',
        plugins=dict(root='bot/plugins')
    ) for session_name in session_names]

    return tg_clients

async def get_tg_web_data(tg_client) -> str:
    async with tg_client:
        user_data = await tg_client.get_me()

    logger.success(f'Session added successfully @{user_data.username} | {user_data.first_name} {user_data.last_name}')
    try:
        if not tg_client.is_connected:
            try:
                await tg_client.connect()
            except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                raise InvalidSession(session_name)

        web_view = await tg_client.invoke(RequestWebView(
            peer=await tg_client.resolve_peer('quackquack_game_bot'),
            bot=await tg_client.resolve_peer('quackquack_game_bot'),
            platform='android',
            from_bot_menu=False,
            url='https://api.quackquack.games/'
        ))

        auth_url = web_view.url
        tg_web_data = unquote(
            string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0])

        if tg_client.is_connected:
            await tg_client.disconnect()
        print("tg_web_data",tg_web_data)
        return tg_web_data

    except InvalidSession as error:
        raise error

    except Exception as error:
        logger.error(f"{session_name} | Unknown error during Authorization: {error}")
        await asyncio.sleep(delay=3)

async def run():
    headers = {
            'Accept': '*/*',
            'Accept-Language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
            'Connection': 'keep-alive',
            'Origin': 'https://play.quackquack.games/',
            'Referer': 'https://play.quackquack.games/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
            'sec-ch-ua': '"Microsoft Edge";v="123", "Not:A-Brand";v="8", "Chromium";v="123", "Microsoft Edge WebView2";v="123"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
    }

    clients = await get_tg_clients()

    headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'origin': 'https://play.quackquack.games',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://play.quackquack.games/',
    'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    for client in clients:
        tg_web_data = await get_tg_web_data(client)

        payload = dict(parse.parse_qsl(tg_web_data))
        payload['user'] = json.loads(payload['user'])
        print(json.dumps(payload))
        response =  requests.post('https://api.quackquack.games/auth/telegram-login',data=json.dumps(payload),headers=headers)
        token = response.json()['data']['token']
        while True:
            headers['authorization'] = f'Bearer {token}'
            response =  requests.get('https://api.quackquack.games/nest/list',headers=headers)
            data = response.json().get('data').get('nest')
            nest_ids = [i.get('id') for i in data]
            claim_header = headers
            claim_header['content-type']= 'application/x-www-form-urlencoded'
            for i in nest_ids:
                sleep(1)
                response =  requests.post('https://api.quackquack.games/nest/collect',headers=claim_header, data=f'nest_id={i}')
                print(response.json())
            sleep(10)
asyncio.run(run())