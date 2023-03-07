import asyncio
import signal
import nio
import fire
import os

class Bot:
    def init(self, matrix_user, matrix_access_token, matrix_server, post_room, join_on_invite, leave_empty_rooms):
        self.matrix_user=matrix_user
        self.matrix_access_token=matrix_access_token
        self.matrix_server=matrix_server
        self.post_room=post_room
        self.join_on_invite=join_on_invite
        self.leave_empty_rooms=leave_empty_rooms
        self.client = nio.AsyncClient(homeserver=self.matrix_server, user=self.matrix_user)
        self.client.access_token = self.matrix_access_token

    async def private_image_cb(self, room, event):
        print(event) #TODO
    
    async def poll_cb(self, room, event):
        print(event) #TODO

    async def invite_cb(self, room, event):    
        if self.join_on_invite:
            result = await self.client.join(room.room_id)
            for attempt in range(3):
                if type(result) == nio.JoinError:
                    print(f'attempt {attempt} failed')
                else:
                    return
    
    async def memberevent_cb(self, room, event):
        if room.member_count == 1 and event.membership=='leave' and event.sender != self.matrix_user:
            await self.client.room_leave(room.room_id)

    async def send_message(self, message):
        return await self.send_text(self.post_room, message) #TODO
    
    async def send_image(self, image):
        None
        # return await self.send_image(room, matrix_uri, text, event, mimetype, w, h, size) #TODO
    
    async def run(self):
        sync_response = await self.client.sync()
        if type(sync_response) == nio.SyncError:
            print(f'Received Sync Error when trying to do initial sync! Error message is: {sync_response.message}')
        else:
            for roomid, room in self.client.rooms.items():
                if len(room.users) == 1 and self.leave_empty_rooms:
                    await self.client.room_leave(roomid)

            if self.client.logged_in:
                self.client.add_event_callback(self.private_image_cb, nio.events.room_events.RoomMessageImage)
                self.client.add_event_callback(self.invite_cb, nio.events.invite_events.InviteEvent)
                self.client.add_event_callback(self.poll_cb, nio.events.room_events.Event)
                
                self.bot_task = asyncio.create_task(self.client.sync_forever(timeout=30000))
                await self.bot_task
            else:
                print('Client was not able to log in, check env variables!')

    def handle_exit(self):
        self.bot_task.cancel()

async def main(matrix_user=os.getenv('MATRIX_USER'), 
               matrix_access_token=os.getenv('MATRIX_ACCESS_TOKEN'), 
               matrix_server=os.getenv('MATRIX_SERVER', 'http://localhost:8008'), 
               post_room=os.getenv('MATRIX_POST_ROOM'), 
               join_on_invite=os.getenv('MATRIX_JOIN_ON_INVITE', 'true').lower() == 'true',
               leave_empty_rooms=os.getenv('MATRIX_LEAVE_EMPTY_ROOMS', 'true').lower() == 'true'):
    
    if matrix_user and matrix_access_token and post_room:
        bot=Bot()
        bot.init(matrix_user, matrix_access_token, matrix_server, post_room, join_on_invite, leave_empty_rooms)

        loop=asyncio.get_running_loop()

        for signame in {'SIGINT', 'SIGTERM'}:
            loop.add_signal_handler(
                getattr(signal, signame),
                bot.handle_exit)
            
        await bot.run()

        try:
            await bot.client.close()
        except Exception as e:
            print(f'Error while closing client: {e}')

    else:
        print("Bot needs a MATRIX_USERNAME, MATRIX_ACCESS_TOKEN, and POST_ROOM to run. These can be provided in the command line or as environment variables.")


if __name__ == "__main__":
    fire.Fire(main)