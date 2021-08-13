from telethon import client
from telethon.sync import TelegramClient, events
from telethon.tl.custom.button import Button
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerChat, InputPeerEmpty
from Context import Context
from repositories.WorkerRepository import WorkerRepository as wr
from telethon.tl.types import Channel,ChatForbidden,Chat, PeerChannel, PeerChat
from telethon.tl.functions.messages import AddChatUserRequest
from telethon.tl.functions.channels import InviteToChannelRequest

api_id = "4540261"
api_hash = "8627c4e0ef04c5cd61afcee91bdaa7de"
bot_token = "838625601:AAGPCiCKXJ0NJbEj1aI65zjMIpQDipyglUc"

bot = TelegramClient('bot', api_id, api_hash)
bot.start(bot_token=bot_token)
class setting:
    Type=""
    Id=0
    Phone=""
@bot.on(events.NewMessage(pattern="/start"))
async def handler(event):
    print(event.raw_text)
    buttons = [
        [
            Button.text(" List of groups ", resize=True),
            Button.text(" Registration number ", resize=True),
        ],
        [
            Button.text(" Registration number ", resize=True)
        ]
    ]
    msg = "What can I do for you ??"
    await event.client.send_message(event.chat_id, msg, buttons=buttons)


@bot.on(events.NewMessage(pattern="(List of groups)"))
async def addGroup(event):
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("Please send your number")
        phone = await conv.get_response()
        phone = phone.message
        setting.Phone = phone
        client = TelegramClient(phone,api_id,api_hash)
        await client.connect()
        if await client.is_user_authorized():
            result = await client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=200,
                hash=0
            ))
            msg = ""
            for r in result.chats:
                print(type(r))
                print(r)
                if type(r)==Chat:
                    m = F"\n Title: {r.title}\n ID: {r.id}\n /run_{r.id}_group"
                    msg += m
                elif  (type(r)==Channel and r.megagroup==True):
                    m = F"\n Title: {r.title}\n ID: {r.id}\n /run_{r.id}_mega"
                    msg += m
            await conv.send_message(msg)
        else:
            await conv.send_message("Register your number first")

        await client.disconnect()

@bot.on(events.NewMessage(pattern="(Select a group)"))
async def selectGroup(event):
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("Please send your number")
        phone = await conv.get_response()
        phone = phone.message
        client = TelegramClient(phone,api_id,api_hash)
        await client.connect()
        if await client.is_user_authorized():
            result = await client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=200,
                hash=0
            ))
            msg = ""
            for r in result.chats:
                print(type(r))
                print(r)
                if type(r)==Chat:
                    m = F"\n Title: {r.title}\n ID: {r.id}\n /select_{r.id}_group"
                    msg += m
                elif  (type(r)==Channel and r.megagroup==True):
                    m = F"\n Title: {r.title}\n ID: {r.id}\n /select_{r.id}_mega"
                    msg += m
            await conv.send_message(msg)
        else:
            await conv.send_message("Register your number first")

        await client.disconnect()

@bot.on(events.NewMessage(pattern="(Registration number)"))
async def addWorker(event):
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("Please send your number")
        phone = await conv.get_response()
        phone = phone.message
        worker = TelegramClient(phone, api_id,api_hash)
        await worker.connect()
        if await worker.is_user_authorized():
            await conv.send_message("This number is already registered")
        else:
            send_code = await worker.send_code_request(phone)
            send_code_hash = send_code.phone_code_hash
            await conv.send_message("Please send us the code sent to you by Telegram")
            code = await conv.get_response()
            code = code.message
            code = code[1:]
            print(code)
            await worker.sign_in(phone=phone,code=code,phone_code_hash=send_code_hash)
            await conv.send_message("Successfully registered")
        await worker.disconnect()
@bot.on(events.NewMessage(pattern="/select"))
async def setGroup(event):
    attr = event.raw_text.split("_")
    setting.Id = int(attr[1])
    setting.Type = attr[2]
    await event.client.send_message(event.chat_id,"The group was successfully registered")

@bot.on(events.NewMessage(pattern="/run"))
async def start(event):
    async with bot.conversation(event.chat_id) as conv:
        # await conv.send_message("Please send your number")
        # phone = await conv.get_response()
        phone = setting.Phone
        attr = event.raw_text.split("_")
        worker = TelegramClient(phone, api_id,api_hash)
        await worker.connect()
        if await worker.is_user_authorized():
            dialogs = await worker.get_dialogs()
            target = int(attr[1])
            await conv.send_message("Which member should I start with?")
            memberId = await conv.get_response()
            memberId = int(memberId.message)
            members = []
            if attr[2]=="group":
                targetEntity = await worker.get_input_entity(PeerChat(target))
                members = await worker.get_participants(targetEntity)
            elif attr[2]=="mega":
                targetEntity = await worker.get_input_entity(PeerChannel(target))
                members = await worker.get_participants(targetEntity)
            members = members[memberId:]
            Tried = 0
            added = 0
            dontadded = 0
            for member in members:
                if setting.Type=="group":
                    try:
                        r = await worker(
                        AddChatUserRequest(
                        setting.Id,
                        member,
                        fwd_limit=200  # Allow the user to see the 10 last messages
                        ))
                        added += 1
                        print("added")

                    except Exception as err:
                        print(err)
                        dontadded += 1
                    finally:
                        if(Tried==50):
                            break
                        Tried += 1
                elif setting.Type=="mega":
                    try:
                        myGroupEntity = await worker.get_input_entity(PeerChannel(setting.Id))
                        r = await worker(InviteToChannelRequest(
                        myGroupEntity,
                        [member]
                        ))
                        added =+ 1
                        print("added")
                        print(r)
                    except Exception as err:
                        print(err)
                        dontadded += 1
                    finally:
                        if(Tried==50):
                            break
                        Tried += 1
            await conv.send_message(F"Tried: {Tried}\nAdded: {Tried-dontadded}\nError: {dontadded}")
                    
        else:
            await conv.send_message("Register your number first")
        await worker.disconnect()
print("|Start|")
bot.run_until_disconnected()
