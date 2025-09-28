import json
from channels.generic.websocket import AsyncWebsocketConsumer


class EventsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send_json({"hello": True})

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                data = json.loads(text_data)
            except Exception:
                data = {"raw": text_data}
            await self.send_json({"echo": data})
        elif bytes_data:
            await self.send(bytes_data)

    async def disconnect(self, code):
        pass

    async def send_json(self, payload: dict):
        await self.send(text_data=json.dumps(payload))
