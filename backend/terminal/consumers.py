import asyncio
import json
import select
import threading
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from hosts.models import Host
from hosts.ssh import open_shell


class TerminalConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer bridging the browser terminal and an SSH shell."""

    async def connect(self):
        # Authenticate via JWT token passed as ?token= in the query string.
        query = parse_qs(self.scope.get('query_string', b'').decode())
        token = (query.get('token') or [None])[0]
        self.user = await self._auth(token)
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        self.loop = asyncio.get_event_loop()
        self.client = None
        self.channel = None
        self.thread = None
        self.closed = False
        await self.accept()

    @database_sync_to_async
    def _auth(self, token):
        if not token:
            return None
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from django.contrib.auth import get_user_model
            payload = AccessToken(token)
            return get_user_model().objects.get(pk=payload['user_id'])
        except Exception:
            return None

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return
        action = data.get('action')
        if action == 'connect':
            await self._connect_host(data.get('host_id'))
        elif action == 'input':
            await self._send_input(data.get('data', ''))
        elif action == 'resize':
            await self._resize(data.get('cols', 80), data.get('rows', 24))
        elif action == 'close':
            await self._close_shell()

    async def _connect_host(self, host_id):
        if not host_id:
            await self.send(text_data=json.dumps({'type': 'error', 'data': 'host_id required'}))
            return
        try:
            self.client, self.channel = await database_sync_to_async(self._open)(host_id)
        except Exception as exc:
            await self.send(text_data=json.dumps({'type': 'error', 'data': f'{type(exc).__name__}: {exc}'}))
            return
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()
        await self.send(text_data=json.dumps({'type': 'connected'}))

    def _open(self, host_id):
        host = Host.objects.get(pk=host_id)
        return open_shell(host)

    def _reader(self):
        try:
            while not self.closed:
                r, _, _ = select.select([self.channel], [], [], 0.5)
                if r:
                    data = self.channel.recv(65536)
                    if not data:
                        break
                    self._emit('data', data.decode('utf-8', 'replace'))
        except Exception:
            pass
        finally:
            if not self.closed:
                self._emit('close', '')

    def _emit(self, mtype, data):
        try:
            asyncio.run_coroutine_threadsafe(
                self.send(text_data=json.dumps({'type': mtype, 'data': data})), self.loop)
        except Exception:
            pass

    async def _send_input(self, data):
        if self.channel:
            try:
                await database_sync_to_async(self.channel.send)(data.encode('utf-8'))
            except Exception:
                pass

    async def _resize(self, cols, rows):
        if self.channel:
            try:
                await database_sync_to_async(self.channel.resize_pty)(width=cols, height=rows)
            except Exception:
                pass

    async def _close_shell(self):
        await database_sync_to_async(self._cleanup)()

    def _cleanup(self):
        self.closed = True
        try:
            if self.channel:
                self.channel.close()
        except Exception:
            pass
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass

    async def disconnect(self, code):
        await database_sync_to_async(self._cleanup)()