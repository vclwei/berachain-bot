import time


class Account:
    def __init__(self, address, proxy):
        self.address = address
        self.proxy = proxy
        self.last_claimed_time = 0

    def is_claimable(self):
        return time.time() - self.last_claimed_time > 8*60*60

    def next_claim_time(self):
        return self.last_claimed_time + 8*60*60
