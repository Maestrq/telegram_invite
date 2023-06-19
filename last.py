import asyncio
from pyrogram import Client
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked
from random import randint
from random_strings import random_string
import os
import pymongo
import time
import datetime
from dotenv import load_dotenv
import pickledb
import asyncio
from loguru import logger
import sys
from pyrogram.errors import FloodWait, UserIsBlocked, PeerIdInvalid, UserPrivacyRestricted, UserNotMutualContact, UserDeactivated, UserDeactivatedBan, AuthKeyInvalid, SessionRevoked, AuthKeyUnregistered, UserChannelsTooMuch, PeerFlood
from pyrogram.types import Message

bot = Client('bot')

logger.add('members.log', level="INFO")
load_dotenv()
myclient = pymongo.MongoClient(os.getenv("MONGO_STRING2"))
mydb = myclient["mydatabase"]
accounts = mydb["accounts"]
mb = pickledb.load('used_proxies.db', True)


async def chat_add_people(bot_info, add_users : list, client_chat : str, soucre_chat : str, client_chat_participants : list, owner_id : int):
        proxies = mb.get("not_used")
        proxy = proxies.pop()
        mb.set("not_used", proxies)
        add_bot = Client(random_string(10), session_string=bot_info["session_string"], api_id=1234)
        await add_bot.start()
        bot_name = await add_bot.get_me()
        bot_name = bot_name.first_name
        print(f"bot_name - {bot_name}")
        bot_chats = [dialog.chat.username async for dialog in add_bot.get_dialogs()]
        print(bot_chats[1])
        if client_chat not in bot_chats:
            print('adding to client chat')
            add_bot.join_chat(chat_id=client_chat)
            await asyncio.sleep(2)
        if soucre_chat not in bot_chats:
            print('adding to source chat')
            add_bot.join_chat(chat_id=soucre_chat)
            await asyncio.sleep(2)        
        try:
            while add_users:
                user_for_add = add_users.pop()
                if user_for_add.user.id not in client_chat_participants:
                    if user_for_add.user.username != None:
                        try:
                            await add_bot.add_chat_members(chat_id=client_chat, user_ids=[user_for_add.user.username])
                            logger.info(f"{bot_name} added {user_for_add.user.first_name}")
                        except UserPrivacyRestricted:  #The user’s privacy settings is preventing you to perform this action | Обмежив додавання 
                            logger.error(f"{user_for_add.user.first_name} failed attempt, adding probably disabled ({bot_name})")
                        except PeerIdInvalid as e: # The peer id being used is invalid or not known yet. Make sure you meet the peer before interacting with it
                            print(e)
                        except UserNotMutualContact:   # The provided user is not a mutual contact | Наданий користувач не є взаємним контактом
                            logger.error(f"{user_for_add.user.first_name} failed attempt, The provided user is not a mutual contact ({bot_name})")
                        except UserChannelsTooMuch:
                            logger.error(f"{user_for_add.user.first_name} failed attempt, user have too much channels ({bot_name})")
                        finally:
                            await asyncio.sleep(randint(3,9))
                            client_chat_participants.append(user_for_add.user.id)
        except FloodWait as e:
            print(e.value)
            ban_time = e.value + e.value / 100 * randint(5, 20)
            unban_time = time.time() + ban_time
            accounts.update_one({"_id" : bot_info["_id"]}, {'$set' : {"Suspended" : True, "unban_time" : unban_time}})
            logger.error(f"{bot_name} banned for {ban_time}")
            print(f"{bot_name} banned for {ban_time}")    
        except UserIsBlocked:
            print(f"{bot_name} banned forever")
            logger.error(f"{bot_name} banned forever")
            accounts.delete_one({"_id" : bot_info["_id"]})
        except UserDeactivated:
                print('UserDeactivated')
                accounts.delete_one({"_id" : bot_info["_id"]})
                await bot.send_message(owner_id, 'Акаунт забанили')
        except UserDeactivatedBan:
            print('UserDeactivatedBan')
            accounts.delete_one({"_id" : bot_info["_id"]})
            await bot.send_message(owner_id, 'Акаунт забанили')
        except AuthKeyInvalid:
            print('AuthKeyInvalid')
            accounts.update_one({"_id": bot_info['_id']}, {"$set": {'Suspended': True}})
            await bot.send_message(owner_id, 'Сесію розлогінили')
        except SessionRevoked:
            print('SessionRevoked')
            accounts.update_one({"_id": bot_info['_id']}, {"$set": {'Suspended': True}})
            await bot.send_message(owner_id, 'Сесію розлогінили')
        except AuthKeyUnregistered:
            print('AuthKeyUnregistered')
            accounts.update_one({"_id": bot_info['_id']}, {"$set": {'Suspended': True}})
            await bot.send_message(owner_id, 'Сесію розлогінили')
        except PeerFlood:
            if accounts.find_one({'_id' : bot_info['_id']})['flood'] == False:
                accounts.update_one({"_id" : bot_info['_id']}, {"$set" : {"Suspended" : True, "unban_time" : 172800 + time.time()}, 'flood' : True})
            else:
                accounts.delete_one({'_id' : bot_info['_id']})
                await bot.send_message(owner_id, text=f"{bot_name} spamblock")
        except Exception as e:
            print(e)
        await add_bot.stop()
        print('finish')


@bot.on_message(filters.command(["add"]))
async def add_people2(client, message):
    #['gateio', 'lviv_today', '1'] 
    data_list = message.text.split(" ")[1:]
    source_chat = data_list[0]
    client_chat = data_list[1]
    bots_num = int(data_list[2])
    app = Client("name", session_string=accounts.find_one({"Suspended" : False})['session_string'], api_id=1234)
    await app.start()
    chats = [dialog.chat.username async for dialog in app.get_dialogs()]
    client_chat_participants = [i.user.id async for i in app.get_chat_members(chat_id=client_chat)]
    if source_chat not in chats:
        await app.join_chat(chat_id=source_chat)
    if client_chat not in chats:
        await app.join_chat(chat_id=client_chat)
    add_users = [i async for i in app.get_chat_members(chat_id=source_chat)]
    await app.stop()
    print(add_users[0])
    print('tasks')
    print(client_chat_participants[0])
    tasks = []
    async def main():
        print('async function start')
        for bot_info in accounts.find({"Suspended": False}).limit(bots_num):
            tasks.append(chat_add_people(bot_info=bot_info, add_users=add_users, client_chat=client_chat, client_chat_participants=client_chat_participants, soucre_chat=source_chat, owner_id=message.chat.id))
        await asyncio.gather(*tasks)
    await main()

@bot.on_message(filters.document)
async def loadsession(client, message):
    file_path = f"./{message.document.file_name}"
    if message.document.file_name.endswith('.session'):
        await bot.download_media(message=message, file_name = file_path)
        session_name = str(message.document.file_name).replace('.session', '')
        await bot.send_message(message.chat.id, text=f"{session_name} was saved, trying to add user")   
        try:
            app = Client(session_name, api_id=1234)
            await app.start()
            await bot.send_message(message.chat.id, text=f"User was added to active users!\n {await app.get_me()}")
            user_data = await app.get_me()
            session_str = await app.export_session_string()
            user_data_for_send = {"username" : user_data.first_name,
                                  "phone_number" : user_data.phone_number,
                                  "session_string" : str(session_str),
                                  "date" : time.time(),
                                  "Suspended" : False,
                                  "telegram_id" : user_data.id,
                                  "flood" : False
                                  }
            await app.stop()
            accounts.insert_one(user_data_for_send)
        except Exception as e:
            await bot.send_message(message.chat.id, f"Attemption failed, cause -> {e}")
        finally:
            os.remove(f"./{message.document.file_name}")


@bot.on_message(filters.command(["user_find"]))
async def send_info(client, message):
    username = message.text.split(" ")[1]
    try:
        user = accounts.find_one({"username" : username})
        mes = f"""
I found him!
Username : {user["username"]}
phone number : {user["phone_number"]} 
date when he was added : {datetime.datetime.fromtimestamp(user["date"]).strftime("%Y-%m-%d %H:%M:%S")}         
               """
        await bot.send_message(message.chat.id, text=mes)
    except Exception as e:
        await bot.send_message(message.chat.id, text=f"It does not exist, {e}")


@bot.on_message(filters.command(["get_list"]))
async def sending_list(client, message):
    settings = {"username" : 1}
    users = accounts.find({}, settings)
    await bot.send_message(message.chat.id, text="\n".join([f'{i+1}. {user["username"]}, `{user["telegram_id"]}`' for i, user in enumerate(users)]))


@bot.on_message(filters.command(["bots_info"]))
async def avaliable_or_not(client, message):
    msg = f"currently avaliable: {accounts.count_documents({'Suspended' : False})}\nNot available: {accounts.count_documents({'Suspended' : True})}"
    await bot.send_message(message.chat.id, text=msg)

@bot.on_message(filters.command(['delete']))
async def delete_user(client, message):
    for_delete = message.text.split(' ')[1]
    accounts.delete_one({'telegram_id' : for_delete})
    await bot.send_message(message.chat.id, text=f'account {for_delete} deleted ')

@bot.on_message(filters.command(['logs']))
async def get_logs(client : Client, message : Message):
    await bot.send_document(message.chat.id, document='members.log')
    

bot.run()