import tinytuya
import asyncio

class LedvanceOrbisDevice:
    def __init__(self, device_id, ip, local_key):
        self.device = tinytuya.BulbDevice(device_id, ip, local_key)

    async def turn_on(self):
        await asyncio.to_thread(self.device.turn_on)
    
    async def turn_off(self):
        await asyncio.to_thread(self.device.turn_off)
    
    async def get_status(self):
        return await asyncio.to_thread(self.device.status)
