import asyncio
import random
from loguru import logger

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
            tasks.append(claim_berachain(account, semaphore))
        await asyncio.gather(*tasks)
        sleep_time = random.randint(28160, 30600)
        logger.info(f"Sleeping for {sleep_time} seconds")
        await asyncio.sleep(sleep_time)

async def claim_berachain(account: Account, semaphore: asyncio.Semaphore):
    async with semaphore:
        try:
            run_delay = random.uniform(5, 30)
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
                    logger.info(f"Claim: {account.address} status={r.status_code}")
                else:
                    logger.error(f"Claim: {account.address} status={r.status_code} {r.text}")

        except Exception as e:
            logger.error(f"Claim: {account.address} error={e}")
         

if __name__ == "__main__":
    asyncio.run(main())
