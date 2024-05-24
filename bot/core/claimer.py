import asyncio
import json
from time import time
from datetime import datetime
from urllib import parse
from urllib.parse import unquote
import requests
import aiohttp
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered
from pyrogram.raw.functions.messages import RequestWebView

from bot.config import settings
from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers


class Claimer:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client

    async def get_tg_web_data(self, proxy: str | None) -> str:
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            web_view = await self.tg_client.invoke(RequestWebView(
                peer=await self.tg_client.resolve_peer('quackquack_game_bot'),
                bot=await self.tg_client.resolve_peer('quackquack_game_bot'),
                platform='android',
                from_bot_menu=False,
                url='https://api.quackquack.games/'
            ))

            auth_url = web_view.url
            tg_web_data = unquote(
                string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0])

            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def login_telegram(self, tg_web_data: str) -> str:
        try:
            payload = dict(parse.parse_qsl(tg_web_data))
            payload['user'] = json.loads(payload['user'])
            print(json.dumps(payload))
            response =  requests.post('https://api.quackquack.games/auth/telegram-login',data=json.dumps(payload),headers=headers)
            token = response.json()['data']['token']
            return token
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when getting Profile Data: {error}")
            await asyncio.sleep(delay=3)


    async def send_claim(self, http_client: aiohttp.ClientSession) -> bool:
        try:
            response = await http_client.get('https://api.quackquack.games/nest/list', json={})
            response.raise_for_status()
            data = await response.json()
            data = data.get('data').get('nest')

            nest_ids = [i.get('id') for i in data]

            claim_header = http_client.headers.copy()
            claim_header['content-type']= 'application/x-www-form-urlencoded'
            for i in nest_ids:
                asyncio.sleep(1)
                response =  requests.post('https://api.quackquack.games/nest/collect',headers=claim_header, data=f'nest_id={i}')
                print(response.json())
            asyncio.sleep(10)
            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Claiming: {error}")
            await asyncio.sleep(delay=30)

            return False

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def run(self, proxy: str | None) -> None:
        access_token_created_time = 0
        claim_time = 0
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
            if proxy:
                await self.check_proxy(http_client=http_client, proxy=proxy)

            while True:
                try:
                    if time() - access_token_created_time >= 3600:
                        tg_web_data = await self.get_tg_web_data(proxy=proxy)
                        token = await self.login_telegram(tg_web_data)
                        # http_client.headers["telegram-data"] = tg_web_data
                        http_client.headers['authorization'] = f'Bearer {token}'
                        # headers["telegram-data"] = tg_web_data

                        access_token_created_time = time()

                        mining_data = await self.send_claim(http_client=http_client)

                        # last_claim_time = mining_data['data']['last_claim']
                        

                        # logger.info(f"{self.session_name} | Last claim time: {last_claim_time}")


                        # status = await self.send_claim(http_client=http_client)
                        # #await asyncio.sleep(delay=settings.SLEEP_BETWEEN_CLAIM)
                        # if status:
                        #     mining_data = await self.get_mining_data(http_client=http_client)


                        #     logger.success(f"{self.session_name} | Successful claim | ")

                        #     claim_time = time()


                except InvalidSession as error:
                    raise error

                except Exception as error:
                    logger.error(f"{self.session_name} | Unknown error: {error}")
                    await asyncio.sleep(delay=3)

                else:
                    logger.info(f"Sleep 1min")
                    await asyncio.sleep(delay=60)


async def run_claimer(tg_client: Client, proxy: str | None):
    print("okee")
    try:
        await Claimer(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
