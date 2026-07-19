import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class FetcherProgressConsumer(AsyncJsonWebsocketConsumer):
    group = "fetcher_progress"

    async def connect(self):
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def fetcher_progress_update(self, event):
        await self.send_json(event["data"])
