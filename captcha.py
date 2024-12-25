import asyncio
from capmonster_python import TurnstileTask

CAPTCHA_PARAMS = {
    'website_key': '0x4AAAAAAARdAuciFArKhVwt',
    'website_url': 'https://bartio.faucet.berachain.com/'
}

class ServiceCapmonster:
    def __init__(self, api_key, user_agent):
        self.capmonster = TurnstileTask(api_key)
        self.capmonster.set_user_agent(user_agent)

    def get_captcha_token(self):
        task_id = self.capmonster.create_task(
            **CAPTCHA_PARAMS
        )
        return self.capmonster.join_task_result(task_id).get("token")

    async def get_captcha_token_async(self):
        return await asyncio.to_thread(self.get_captcha_token)

    # Add alias for compatibility
    async def solve_captcha(self):
        return await self.get_captcha_token_async()