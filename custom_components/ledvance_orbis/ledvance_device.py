import tinytuya

class LedvanceOrbisDevice:
    def __init__(self, device_id, ip, local_key):
        self.device = tinytuya.BulbDevice(device_id, ip, local_key)

    def turn_on(self):
        self.device.turn_on()
    
    def turn_off(self):
        self.device.turn_off()
    
    def get_status(self):
        return self.device.status()
