import simplematrixbotlib as botlib
import nio
import os
import fire

polls = {}

def main(botname, password, postroom, serveraddress="http://localhost:8008"):
    creds = botlib.Creds(serveraddress, botname, password)
    bot = botlib.Bot(creds)
    asyn_bot = nio.AsyncClient(serveraddress, botname)

    @bot.listener.on_custom_event(nio.events.room_events.Event)
    async def on_poll_message(room, event):
        response = await asyn_bot.login(password)
        match = botlib.MessageMatch(room, event, bot)
        if match.is_not_from_this_bot() and room.is_group and room.member_count == 2:
            match event.source['type']:
                case "org.matrix.msc3381.poll.start":
                    event_id = event.source['content']['org.matrix.msc3381.poll.start']['question']['body']
                    polls[event.event_id] = event_id
                    await bot.api.send_text_message(room.room_id, f'Poll: {event_id} started.\n')
                case "org.matrix.msc3381.poll.response":
                    event_id = event.source["content"]["m.relates_to"]["event_id"]
                    sender = event.source["sender"]
                    if event_id in polls:
                        await bot.api.send_text_message(room.room_id, f'User: {sender}\n responded to poll: {polls[event_id]}\n')
                case "org.matrix.msc3381.poll.end":
                    event_id = event.source["content"]["m.relates_to"]["event_id"]
                    results = event.source['content']['body']
                    if event_id in polls:
                        await bot.api.send_text_message(room.room_id, f'{polls[event_id]}: {results}\n')
                        del polls[event_id]
                case _:
                    await bot.api.send_text_message(room.room_id, "Unknown Event")
            print(event)

    @bot.listener.on_custom_event(nio.events.room_events.RoomMessageImage)
    async def on_image_message(room, event):
        response = await asyn_bot.login(password)
        match = botlib.MessageMatch(room, event, bot)
        if match.is_not_from_this_bot() and room.is_group and room.member_count == 2:
            url = event.url
            urllist = url.split("/")
            response = await asyn_bot.download(urllist[2], urllist[3])
            fname="./"+event.source['content']['body']
            with open(fname, 'wb') as binary_file:
                binary_file.write(response.body)
                binary_file.close()
            if isinstance(response, nio.responses.DownloadError):
                await bot.api.send_text_message(room.room_id, "Bot image retrieval failed. Try again.")
                pass
            else:
                await bot.api.send_image_message(postroom, fname)

                msg_type = 'org.matrix.msc3381.poll.start'

                pollContent = {
                    'org.matrix.msc3381.poll.start': {
                        'question': {
                            'org.matrix.msc1767.text': 'testq',
                                'body': 'testq', 
                                'msgtype': 'm.text'},
                            'kind': 'org.matrix.msc3381.poll.disclosed', 
                            'max_selections': 1, 
                            'answers': [
                                {'id': 'PPDmEEjtpchpbC3u', 'org.matrix.msc1767.text': 'testa'}, 
                                {'id': 'TNjfj4jEoF6zjzRe', 'org.matrix.msc1767.text': 'testb'}]}
                }

                await asyn_bot.room_send(postroom, msg_type, pollContent, ignore_unverified_devices=False)

                os.remove(fname)

    bot.run()

if __name__=="__main__":
    fire.Fire(main)