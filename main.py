import asyncio
import random
import time
from loguru import logger
import re
import json

from account import Account
from captcha import ServiceCapmonster
from curl_cffi.requests import AsyncSession
from config import Config

def fetch_accounts():
    accounts = []
    with open('account.txt', 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            address, proxy = line.split(',')
            accounts.append(Account(address, proxy))

    return accounts

async def main():
    accounts = fetch_accounts()
    semaphore = asyncio.Semaphore(32)

    while True:
        random.shuffle(accounts)
        tasks = []
        for account in accounts:
            if account.is_claimable():
                tasks.append(claim_berachain(account, semaphore))
            else:
                local_time = time.localtime(account.next_claim_time())
                logger.info(f"NoClaimable: {account.address} next_claim_time={time.strftime('%H:%M:%S', local_time)}")
        if len(tasks) > 0:
            await asyncio.gather(*tasks)
        sleep_time = random.randint(65*60, 75*60)
        logger.info(f"CheckAfter: {sleep_time}s")
        await asyncio.sleep(sleep_time)

async def claim_berachain(account: Account, semaphore: asyncio.Semaphore):
    async with semaphore:
        try:
            run_delay = random.uniform(10, 120)
            logger.info(f"Claim: {account.address} proxy={account.proxy} delay={run_delay}s")
            await asyncio.sleep(run_delay)

            token = await ServiceCapmonster(Config().config['capmonster_api_key'],
                                            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36').solve_captcha()
            session = AsyncSession(impersonate="chrome131",
                            proxies={"http": account.proxy, "https": account.proxy}, 
                            timeout=10)
            headers = {
                'authority': 'bartiofaucet.berachain.com',
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'accept-language': 'en-US;q=0.9,en;q=0.8',
                'authorization': f'Bearer {token}',
                'content-type': 'text/plain;charset=UTF-8',
                'origin': 'https://bartio.faucet.berachain.com',
                'priority': 'u=1, i',
                'referer': 'https://bartio.faucet.berachain.com/',
                'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            };
            async with session as s:
                r = await s.post("https://bartiofaucet.berachain.com/api/claim", 
                                 headers=headers, 
                                 params={"address": account.address},
                                json={"address": account.address})
                if r.ok:
                    logger.success(f"ClaimSuccess: {account.address} status={r.status_code}")
                    account.last_claimed_time = time.time()
                elif r.status_code == 429:
                    resp = r.json()
                    wait_time = resp['msg'].split('wait ')[-1].split(' before')[0]
                    hours = int(re.findall(r'(\d+)h', wait_time)[0]) if 'h' in wait_time else 0
                    minutes = int(re.findall(r'(\d+)m', wait_time)[0]) if 'm' in wait_time else 0 
                    seconds = int(re.findall(r'(\d+)s', wait_time)[0]) if 's' in wait_time else 0
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                    account.last_claimed_time = time.time() - (8*60*60 - total_seconds)
                    logger.warning(f"ClaimRateLimit: {account.address} status={r.status_code} wait_time={wait_time} {resp['msg']}")
                else:
                    logger.error(f"ClaimError: {account.address} status={r.status_code} {r.text}")

        except Exception as e:
            logger.error(f"ClaimError: {account.address} error={e}")
         

if __name__ == "__main__":
    asyncio.run(main())
