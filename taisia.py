import asyncio
import datetime
import json
import os
import random
import re
import traceback
from collections import Counter
from contextlib import suppress
from random import choice, choices, randint
from urllib.parse import ParseResult, urlencode, urlunparse

import aiohttp
import discord
import pymongo
import requests
from bs4 import BeautifulSoup
from discord.errors import HTTPException
from discord.flags import Intents
from discord.utils import get
from pymongo import MongoClient

from settings import Settings
from taisia_dict import taisia_dict

settings = Settings()
intents = Intents.default()
intents.reactions = True
intents.members = True
intents.presences = True
intents.message_content = True
client = discord.Client(intents=intents)
votes = {}
banned_maps = []
already_voted = []
yobanii_v_rot = False
one_percent_ban = [False]
magic_word = "1488"
gambling_code = "папуас"
last_activity = datetime.datetime.now() - datetime.timedelta(minutes=16)
last_topic = datetime.datetime.now() - datetime.timedelta(minutes=16)
next_activity = 0
next_topic = 0
server = taisia_dict["IDList"]["ServerID"][0]
stngrm = taisia_dict["IDList"]["ChatIDs"][0]
acdm = taisia_dict["IDList"]["ChatIDs"][1]
krtlshn = taisia_dict["IDList"]["ChatIDs"][2]
ptfn = taisia_dict["IDList"]["ChatIDs"][3]
Taechka = taisia_dict["IDList"]["UserIDs"][0]
Mark = taisia_dict["IDList"]["UserIDs"][1]
Anton = taisia_dict["IDList"]["UserIDs"][2]
Prodavan = taisia_dict["IDList"]["UserIDs"][3]
Nikita = taisia_dict["IDList"]["UserIDs"][4]
Ilya = taisia_dict["IDList"]["UserIDs"][5]
Dora = taisia_dict["IDList"]["UserIDs"][6]
SD = taisia_dict["IDList"]["UserIDs"][7]
Valera = taisia_dict["IDList"]["UserIDs"][8]
watching_saloon = taisia_dict["TaisiaActivities"]["watching"][0]
announcement_message = taisia_dict["IDList"]["message_IDs"][0]
msg_votemap = None
vc = None
EndEvent = asyncio.Event()
ExpectingCaseName = False
UserExpectingCase = None
map_bans_msg = None
caserollin = False
gamblelimit = 0
banek_count = 1040
case_key_price = 180


def get_database():
    from pymongo import MongoClient

    client = MongoClient(settings.mongodb_dsn)
    return client["taisia"]


taisia_db = get_database()


def send_msg(text, channel):  # чтобы покороче
    asyncio.get_event_loop().create_task(channel.send(text))


def PrintCurrTime(comment):
    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print(comment, current_time)


def CaseTrunc(n, k):  # округление для флоатов предметов из кейса
    return int(n * k) / k


def replacenth(
    string, sub, wanted, n
):  # замена н-ного появления паттерна на что-то
    where = [m.start() for m in re.finditer(sub, string)][n - 1]
    before = string[:where]
    after = string[where:]
    after = after.replace(sub, wanted, 1)
    newString = before + after
    return newString


def chislitelnoye(numbah):
    last_numbah = numbah % 10
    last_numbas = numbah % 100
    if last_numbas > 10 and last_numbas < 21:
        return "дней"
    elif last_numbah == 1:
        return "день"
    elif last_numbah == 2 or last_numbah == 3 or last_numbah == 4:
        return "дня"
    else:
        return "дней"


async def Chooser(task, chan, cont):  # рандомбот
    if task == "choose":
        if cont.count(",") > 1:
            choonser = cont.split(" ", 2)[2].split(", ")
        else:
            choonser = cont.split(" ")[2:]
        if " или " in choonser:
            choonser = choonser.replace(" или ", " ")
        embed = discord.Embed(
            colour=discord.Color.from_rgb(
                randint(0, 255), randint(0, 255), randint(0, 255)
            )
        )  # title=None, description=None,
        embed.add_field(
            name=random.choice(choonser),
            value=random.choice(taisia_dict["ChooserList"]),
        )
        await chan.send(embed=embed)

    elif task == "colour":
        color = discord.Color.from_rgb(
            randint(0, 255), randint(0, 255), randint(0, 255)
        )  # also a hex
        embed = discord.Embed(colour=color)  # title=None, description=None,
        embed.add_field(name="RGB:", value=f"{color.r}, {color.g}, {color.b}")
        embed.add_field(name="HEX:", value=color)
        embed.add_field(
            name="Подробнее:", value=f"`color-hex.com/color/{str(color)[1:]}`"
        )
        await chan.send(embed=embed)

    elif task == "yesorno":
        if randint(0, 1):
            embed = discord.Embed(
                colour=discord.Color.from_rgb(
                    randint(0, 99), 255, randint(0, 99)
                )
            )
            embed.add_field(
                name=random.choice(["Да.", "Да!", "Ага.", "Ну да.."]),
                value=f"*{random.choice(taisia_dict['ChooserList'])}*",
            )
            await chan.send(embed=embed)
        else:
            embed = discord.Embed(
                colour=discord.Color.from_rgb(
                    255, randint(0, 99), randint(0, 99)
                )
            )
            embed.add_field(
                name=random.choice(["Нет.", "Нет!", "Не-а.", "Ну не.."]),
                value=f"*{random.choice(taisia_dict['ChooserList'])}*",
            )
            await chan.send(embed=embed)


def votemap_random(msg__votemap):
    global vc
    global votes
    global yobanii_v_rot
    global map_bans_msg
    global banned_maps
    global one_percent_ban
    global msg_votemap
    global already_voted
    res = "Agency"
    players = votes[msg_votemap.id]["players"]
    maps = votes[msg_votemap.id]["maps"]

    if maps:
        if banned_maps:
            maps[:] = (elem for elem in maps if str(elem) not in banned_maps)
        if maps:
            res = str(choice(maps))
            if len(maps) > 1:
                if (
                    len(maps) == 5
                    and Counter(maps).most_common(1)[0][1] == 4
                    and str(Counter(maps).most_common(2)[1][0]) == res
                ):
                    yobanii_v_rot = True
    else:
        del votes[msg_votemap.id]  # потому что глобальная
        return random.choice(taisia_dict["ErrorList"])
        if vc:
            vc.stop()
    if [user for user in taisia_dict["CS"] if user in players] and randint(
        0, 1
    ):
        MapPickPhrases = taisia_dict["CS"][
            random.choice(
                [user for user in taisia_dict["CS"] if user in players]
            )
        ]
    else:
        MapPickPhrases = taisia_dict.get(
            res,
            [
                "Как вы это сделали?",
                "У меня для неё даже нет эмодзи...",
                "Смешно.",
                "Сами себя и обдурили...",
            ],
        )

    del votes[msg_votemap.id]  # потому что глобальная
    if vc:
        vc.stop()
        if yobanii_v_rot:
            vc.play(
                discord.FFmpegPCMAudio(
                    executable=settings.ffmpeg_path,
                    source=os.path.join(
                        settings.music_files_folder, "kazino.mp3"
                    ),
                )
            )
            vc.source = discord.PCMVolumeTransformer(vc.source, volume=0.7)
        else:
            vc.play(
                discord.FFmpegPCMAudio(
                    executable=settings.ffmpeg_path,
                    source=os.path.join(
                        settings.music_files_folder,
                        f"{(re.search(r':(.+?):', res).group(1))}.mp3"
                        or "VoteEnd.mp3",
                    ),
                )
            )
            vc.source = discord.PCMVolumeTransformer(vc.source, volume=0.3)

    if one_percent_ban[0] and res in one_percent_ban:
        send_msg(
            f"Поздравляю, вы попали в 1% и {res} не была забанена. Повезло-повезло!",
            msg_votemap.channel,
        )

    yobanii_v_rot = False
    banned_maps = []
    map_bans_msg = None
    one_percent_ban[0] = False
    one_percent_ban = one_percent_ban[:1]
    already_voted = []

    return (
        random.choice(taisia_dict["DepartingList"])
        + res
        + ". "
        + random.choice(MapPickPhrases)
    )


async def ChangeActivity():
    global last_activity
    global watching_saloon
    global next_activity
    if datetime.datetime.now() - last_activity > datetime.timedelta(
        minutes=next_activity
    ):
        next_activity = randint(11, 75)
        print(f"Activity cooldown is set to {next_activity}")
        if not randint(0, 4):
            await client.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching, name="за салоном."
                )
            )
            last_activity = datetime.datetime.now()
            PrintCurrTime(
                f"Activity changed to «следит за салоном.» at".format(client)
            )
        else:
            whattodo = random.choice(
                list(taisia_dict["TaisiaActivities"].keys())
            )
            watching_saloon = random.choice(
                list(taisia_dict["TaisiaActivities"][whattodo])
            )
            await client.change_presence(
                activity=discord.Activity(
                    type=getattr(discord.ActivityType, whattodo),
                    name=watching_saloon,
                )
            )
            last_activity = datetime.datetime.now()
            PrintCurrTime(
                f"Activity changed to «{whattodo} {watching_saloon}» at".format(
                    client
                )
            )
        if not randint(0, 4):
            included_extensions = ["jpeg", "png"]
            taisiafaces = [
                fn
                for fn in os.listdir(settings.face_file_folder)
                if any(fn.endswith(ext) for ext in included_extensions)
            ]
            with open(
                os.path.join(
                    settings.face_file_folder, random.choice(taisiafaces)
                ),
                "rb",
            ) as f:
                taisiaface = discord.File(f)
                try:
                    await client.user.edit(password=None, avatar=f.read())
                except HTTPException:
                    print("-=Mnogovato avok budet!=-")
            print("Userpic changed to " + taisiaface.filename)


async def ChangeTopic(chat, topic, reason):
    global last_topic
    global next_topic
    if datetime.datetime.now() - last_topic > datetime.timedelta(
        minutes=next_topic
    ):
        next_topic = randint(25, 125)
        print(f"Topic cooldown is set to {next_topic}")
        await client.get_channel(chat).edit(topic=topic, reason=reason)
        print(f"Topic changed to {topic}")
        last_topic = datetime.datetime.now()


async def CheckSus():
    susdate = None
    async with aiohttp.ClientSession() as session:
        suslist = taisia_db["suslist"].find_one()
        for elem in suslist["sus"]:
            async with session.get(elem) as response:
                html = await response.read()
                html = html.decode("utf8", errors="ignore")
                if (
                    re.search(r"profile_ban_status", html, flags=re.DOTALL)
                    and "VAC ban on record" in html
                ):
                    susdate = (
                        datetime.datetime.now()
                        - datetime.datetime.strptime(
                            suslist["sus"][elem]["Date"], "%Y/%m/%d"
                        )
                    ).days

                    susreminder = f"\nНапоминаю: _«{suslist['sus'][elem].get('Comment', '').strip()}»_"
                    suslist["Stat"]["Wait times"].append(susdate)
                    suslist["Stat"]["Banned"] += 1
                    if susdate > suslist["Stat"]["Longest wait"]:
                        suslist["Stat"]["Longest wait"] = susdate

                    send_msg(
                        f"{random.choice(taisia_dict['susCaught'])} Спустя {susdate} суток: {elem}{susreminder}\n<@!{suslist['sus'][elem]['Submitter']}>",
                        client.get_channel(stngrm),
                    )
                    del suslist["sus"][elem]
                    taisia_db["suslist"].update_one(
                        {"_id": suslist["_id"]},
                        {
                            "$set": {
                                "Stat": suslist["Stat"],
                                "sus": suslist["sus"],
                            }
                        },
                    )
                    break
                
                if (
                    re.search(r"profile_ban_status", html, flags=re.DOTALL)
                    and "game ban on record" in html
                    ):
                    susreminder = f"\n_«{suslist['sus'][elem].get('Comment', '').strip()}»_"
                    suslist["Stat"]["Banned"] += 1
                    send_msg(
                        f"{elem}{susreminder}\n<@!{suslist['sus'][elem]['Submitter']}>",
                        client.get_channel(acdm),
                    )
                    print(suslist["sus"][elem]["Date"])
                    print(datetime.datetime.strptime(suslist["sus"][elem]["Date"], "%Y/%m/%d"))
                    del suslist["sus"][elem]
                    taisia_db["suslist"].update_one(
                        {"_id": suslist["_id"]},
                        {
                            "$set": {
                                "Stat": suslist["Stat"],
                                "sus": suslist["sus"],
                            }
                        },
                    )
                    break


@client.event
async def on_ready():
    PrintCurrTime(">>Logged in as {0.user} at".format(client))
    # if client.get_user(Taechka).nick != "Таечка":
    #     asyncio.get_event_loop().create_task(client.get_user(Taechka).edit(nick="Таечка"))
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, name=watching_saloon
        )
    )
    await CheckSus()


@client.event
async def on_connect():
    PrintCurrTime(">>Connected at")


@client.event
async def on_disconnect():
    PrintCurrTime(">>Disconnected at")


@client.event
async def on_resumed():
    PrintCurrTime(">>Resumed connection at")


@client.event
async def on_invite_create(invite):
    PrintCurrTime(">>An invite link was created at")


@client.event
async def on_member_join(member):
    channel = client.get_channel(stngrm)
    send_msg(
        (
            random.choice(taisia_dict["WelcomeList"])
            + f" <@!{member.id}>"
            + random.choice(taisia_dict["WelcomeList2"])
        ),
        channel,
    )


@client.event
async def on_member_remove(member):
    channel = client.get_channel(stngrm)
    send_msg(
        random.choice(taisia_dict["GoodbyeList"])
        + f" <@!{member.id}>. "
        + random.choice(taisia_dict["GoodbyeList2"]),
        channel,
    )


@client.event
async def on_voice_state_update(member, before, after):
    member = taisia_dict["Passports"].get(member.id)

    if (
        before.channel is None
        and after.channel is not None
        and member
        and member["EnterRoom"]
        and (datetime.datetime.now() - member["last_activity"])
        > datetime.timedelta(minutes=15)
    ):
        chlen = member["EnterRoom"]
        if isinstance(chlen, str):
            chlen = [chlen]
        vc = await after.channel.connect()
        entersound = random.choices(
            chlen, member.get("EnterWeights", [1 for _ in chlen])
        )[0]
        vc.play(
            discord.FFmpegPCMAudio(
                executable=settings.ffmpeg_path,
                source=os.path.join(
                    settings.music_files_folder, f"{entersound}.mp3"
                ),
            )
        )
        vc.source = discord.PCMVolumeTransformer(
            vc.source, volume=member["EnterVolume"]
        )
        member["last_activity"] = datetime.datetime.now()
        while vc.is_playing():
            await asyncio.sleep(1)
        await vc.disconnect()

    if (
        before.channel is not None
        and after.channel is None
        and member
        and member["ExitRoom"]
        and (datetime.datetime.now() - member["last_activity"])
        > datetime.timedelta(minutes=15)
        and len(before.channel.members) > 1
    ):
        vc = await before.channel.connect()
        vc.play(
            discord.FFmpegPCMAudio(
                executable=settings.ffmpeg_path,
                source=os.path.join(
                    settings.music_files_folder, f"{member['ExitRoom']}.mp3"
                ),
            )
        )
        vc.source = discord.PCMVolumeTransformer(
            vc.source, volume=member["ExitVolume"]
        )
        member["last_activity"] = datetime.datetime.now()
        while vc.is_playing():
            await asyncio.sleep(1)
        await vc.disconnect()


@client.event
async def on_reaction_add(reaction, user):
    global votes
    global map_bans_msg
    global banned_maps
    global one_percent_ban
    global msg_votemap
    global already_voted

    print(f"_{reaction} {user}")

    if reaction.message.author.id == user.id:
        return

    elif reaction.message == msg_votemap:

        if (
            reaction.emoji == "👍🏻"
            and user
            in client.get_guild(server)
            .get_member(Taechka)
            .voice.channel.members
        ):

            temp_msg_votemap = await reaction.message.channel.fetch_message(
                msg_votemap.id
            )

            if map_bans_msg:
                thumb_dict = {
                    e.emoji: e.count for e in temp_msg_votemap.reactions
                }
                if thumb_dict["👍🏻"] > 3:
                    for elem in temp_msg_votemap.content.split("\n"):
                        if ":" in elem:
                            if (elem[: elem.index(":") + 1]) in list(
                                taisia_dict["Left2VoteList"]
                            ):
                                temp_msg_votemap = await reaction.message.channel.fetch_message(
                                    msg_votemap.id
                                )
                                await reaction.message.edit(
                                    content=temp_msg_votemap.content.replace(
                                        elem,
                                        random.choice(
                                            taisia_dict["AllVotesSentList"]
                                        ),
                                    )
                                )
                                EndEvent.set()
                                return
            else:
                for elem in temp_msg_votemap.content.split("\n"):
                    if elem in list(taisia_dict["Left2VoteList"]):
                        await reaction.message.edit(
                            content=temp_msg_votemap.content.replace(
                                elem,
                                random.choice(taisia_dict["AllVotesSentList"]),
                            )
                        )
                EndEvent.set()
                return

        elif (
            reaction.message.id in votes
            and user
            in client.get_guild(server)
            .get_member(Taechka)
            .voice.channel.members
        ):
            if user.id != Nikita:
                votes[reaction.message.id]["maps"].append(reaction.emoji)
                votes[reaction.message.id]["players"].add(user.id)

            if map_bans_msg:
                await map_bans_msg.add_reaction(reaction)

            if user.id in [
                member.id
                for member in client.get_guild(server)
                .get_member(Taechka)
                .voice.channel.members
            ]:
                already_voted.append(user.id)
                message_content = reaction.message.content
                while True:
                    if "  " not in message_content:
                        break
                    message_content = reaction.message.content.replace(
                        "  ", " "
                    )
                for user_id in already_voted:
                    message_content = message_content.replace(
                        f"<@!{user.id}>", ""
                    )
                await reaction.message.edit(content=message_content)
            if (
                reaction.message.content.split(":")[1] == ""
                and not map_bans_msg
            ):
                print(f"_{reaction.message.content.split(':')[1]}_")
                for elem in reaction.message.content.split("\n"):
                    if elem in list(taisia_dict["Left2VoteList"]):
                        await reaction.message.edit(
                            content=reaction.message.content.replace(
                                elem,
                                random.choice(taisia_dict["AllVotesSentList"]),
                            )
                        )
                        EndEvent.set()

    elif reaction.message == map_bans_msg:
        if (
            user
            in client.get_guild(server)
            .get_member(Taechka)
            .voice.channel.members
        ) and reaction.count > 2:
            temp_msg_votemap = await reaction.message.channel.fetch_message(
                msg_votemap.id
            )
            if randint(0, 99):
                banned_maps.append(str(reaction.emoji))
                if str(reaction.emoji) not in temp_msg_votemap.content:
                    for elem in temp_msg_votemap.content.split("\n"):
                        if elem in list(taisia_dict["awaiting_banned_maps"]):
                            for user_id in already_voted:
                                temp_msg_votemap.content = (
                                    temp_msg_votemap.content.replace(
                                        f"<@!{user.id}>", ""
                                    )
                                )
                            await msg_votemap.edit(
                                content=temp_msg_votemap.content.replace(
                                    elem,
                                    random.choice(
                                        taisia_dict["presenting_banned_maps"]
                                    ),
                                )
                            )
                            temp_msg_votemap = (
                                await reaction.message.channel.fetch_message(
                                    msg_votemap.id
                                )
                            )
                            break
                    await msg_votemap.edit(
                        content=temp_msg_votemap.content
                        + " "
                        + str(reaction.emoji)
                    )
            else:
                one_percent_ban[0] = True
                one_percent_ban.append(str(reaction.emoji))


@client.event
async def on_reaction_remove(reaction, user):
    print("< < Removed:", reaction, user)
    global votes
    global msg_votemap
    global map_bans_msg

    if reaction.message == msg_votemap:
        with suppress(ValueError, KeyError):
            votes[reaction.message.id]["maps"].remove(reaction.emoji)
            votes[reaction.message.id]["players"].remove(user.id)

    # elif reaction.message == map_bans_msg:


@client.event
async def on_member_update(before, after):
    someone = taisia_dict["Passports"].get(before.id, {})
    if someone.get("PreferredName"):
        if (
            before.nick == someone["PreferredName"]
            and after.nick != someone["PreferredName"]
        ):
            await after.edit(
                nick=someone["PreferredName"],
                reason=random.choice(taisia_dict["ReasonList"]),
            )

    if before.id == Taechka and after.nick != "Таечка":
        asyncio.get_event_loop().create_task(after.edit(nick="Таечка"))
        send_msg(
            random.choice(taisia_dict["TaisiaNameChange"]),
            client.get_channel(stngrm),
        )

    await ChangeActivity()

    if not randint(0, 1):
        await CheckSus()

    await ChangeTopic(
        stngrm,
        random.choice(taisia_dict["TopicList"]),
        random.choice(taisia_dict["ReasonList"]),
    )


async def add_reaction(message):
    rand_react = random.choice(
        [
            "<:300iq:817058596092772363>",
            "<:antonio:690712538392035348>",
            "<:wtf:693778630479708231>",
            "🤣",
            "🤔",
            "🤡",
            "😱",
            "👀",
            "🙃",
            "😬",
            "🧐",
        ]
    )
    await asyncio.sleep(randint(0, 8))
    await message.add_reaction(rand_react)


@client.event
async def on_message(message):

    try:
        if message.author.id == Taechka:
            return

        global ExpectingCaseName
        global UserExpectingCase
        global caserollin
        global gamblelimit
        global map_bans_msg
        global msg_votemap
        global case_key_price
        channel = message.channel
        MesCon = message.content

        # лайки, репосты
        if message.attachments and not randint(0, 19):
            await add_reaction(message)

        # исправление дурных привычек
        if [
            elem
            for elem in taisia_dict["Toxicity"]
            if elem.lower() in MesCon.lower()
        ]:
            await message.add_reaction("<:IlyaToxic:745056103095599146>")

        # когда тегают её или роль
        elif (
            "<@!836723365778817034>" in MesCon
            or "<@&703043676552691783>" in MesCon
        ):
            send_msg(random.choice(taisia_dict["MentionList"]), channel)

        elif MesCon.startswith("Тая..?"):
            send_msg(random.choice(taisia_dict["BadHabitList"]), channel)

        elif MesCon.startswith("Таисия, "):
            send_msg(random.choice(taisia_dict["FullNameList"]), channel)

        elif MesCon.startswith("Таисия Андреевна"):
            send_msg(random.choice(taisia_dict["andreevna_list"]), channel)

        elif MesCon.startswith(taisia_dict["TaisiaCAPS"]):
            send_msg(random.choice(taisia_dict["CAPSReaction"]), channel)

        elif MesCon.startswith("!play") and channel != client.get_channel(
            ptfn
        ):
            send_msg(random.choice(taisia_dict["WrongRythm"]), channel)
            await message.add_reaction("🤬")

        elif (
            MesCon.startswith(gambling_code)
            and channel == client.get_channel(acdm)
            and re.search(r"\d+", MesCon)
        ):
            a = re.search(r"\d+", MesCon)[0]
            gamblelimit += int(a)
            print(f"Added {a} to the limit, now it's {gamblelimit}")

        elif any(
            elem in MesCon.lower() for elem in ["ставлю жопу", "жопу ставлю"]
        ):
            send_msg(random.choice(taisia_dict["dont_bet_yo_ass"]), channel)

        if MesCon.startswith("123") and message.author.id == Mark:
            penis = await client.get_channel(krtlshn).fetch_message(
                announcement_message
            )
            vagina = MesCon.replace("123", "")
            await penis.edit(content=vagina)

        # ...и чревовещание
        elif MesCon.startswith(magic_word):
            asyncio.get_event_loop().create_task(
                client.get_channel(stngrm).send(MesCon[len(magic_word) :])
            )

        # атата за меншены и удаление, если
        elif any(elem in MesCon.lower() for elem in ["@everyone", "@here"]):
            if MesCon in ("@here", "@everyone"):
                await message.delete(delay=randint(3, 7))
                deleting_mention = random.choice(
                    taisia_dict["deleting_here/everyone_list"]
                )
            else:
                deleting_mention = ""
            send_msg(
                random.choice(taisia_dict["here_or_everyone_tagged"])
                + deleting_mention,
                channel,
            )

        # ревность
        elif MesCon.startswith("!play") and message.author.id != Taechka:
            if not randint(0, 8):
                send_msg(random.choice(taisia_dict["RythmCuckquean"]), channel)

        elif MesCon.startswith("?choose") and message.author.id != Taechka:
            await Chooser((MesCon[1:]).split()[0], channel, MesCon)
            # await asyncio.sleep(randint(1, 3))
            send_msg(random.choice(taisia_dict["CuckqueanList"]), channel)

        # иногда заступается за Марка
        elif (
            MesCon.startswith("<@!476100337355456552>")
            and message.author.id != Taechka
            and not random.randint(0, 29)
        ):
            send_msg(random.choice(taisia_dict["MarkList"]), channel)

        # Call me by your name
        elif (
            MesCon.startswith(taisia_dict["TaisiaName"])
            and message.author.id != Taechka
        ):

            # #редактирование gamblerslist
            # elif message.author.id == Mark and "каучук" in MesCon.lower():
            #     if re.search(r'\d+', MesCon):
            #         data = taisia_db["gamblerslist"].find_one()
            #         gambler = re.search(r'\d+', MesCon).group()
            #         if str(gambler) in data:
            #             send_msg(data[str(gambler)]["Trophies"], channel)
            #         else:
            #             send_msg("Не вижу такого ID в списке игроков!", channel)
            #     else:
            #         send_msg("Мне нужно ID игрока.", channel)

            # установка стоимости ключа
            if (
                message.author.id == Mark
                and "стоимость ключа" in MesCon.lower()
            ):
                if re.search(r"\d+", MesCon):
                    current_case_key_price = case_key_price
                    case_key_price = re.search(r"\d+", MesCon).group()
                    if case_key_price > 99 and case_key_price < 200:
                        case_key_pretext = "со"
                    else:
                        case_key_pretext = "с"
                    send_msg(
                        f"Стоимость ключа изменена {case_key_pretext} **{current_case_key_price}** на **{case_key_price}**.",
                        channel,
                    )
                else:
                    send_msg(
                        "Стоимость выражается в цифрах, запомню первую в сообщении.",
                        channel,
                    )

            # отслеживание пидорасов
            elif "отследи пидорасов" in MesCon.lower():
                send_msg(
                    "Смотрю...",
                    channel,
                )
                await CheckSus()

            # отчёт
            elif any(
                elem in MesCon.lower()
                for elem in ["моя стат", "мой стат", "мою стат", "моей стат"]
            ):
                # with open("gamblerslist.json", "r", encoding="utf8") as f:
                #     data = json.load(f)
                data = taisia_db["gamblerslist"].find_one()
                if str(message.author.id) in data:
                    embed = discord.Embed(
                        title=f"{(message.author.nick or message.author.name)} открыл: {data[str(message.author.id)]['Opened']}",
                        colour=discord.Color.from_rgb(
                            randint(0, 255), randint(0, 255), randint(0, 255)
                        ),
                    )  # , description=None,
                    for elem in [
                        [
                            "Всего потрачено на кейсы:",
                            round(data[str(message.author.id)]["Spent"], 2),
                        ],
                        [
                            "Заработано:",
                            round(data[str(message.author.id)]["Earned"], 2),
                        ],
                        [
                            "Сальдо:",
                            round(data[str(message.author.id)]["Total"], 2),
                        ],
                        [
                            "Ножей и перчаток:",
                            data[str(message.author.id)]["Tiers"]["Special"],
                        ],
                        [
                            f"Самый ценный трофей ({data[str(message.author.id)]['Trophies'][0][1]} руб.):",
                            data[str(message.author.id)]["Trophies"][0][0],
                        ],
                        [
                            "В среднем:",
                            f"{round((data[str(message.author.id)]['Total'] / data[str(message.author.id)]['Opened']), 2)} руб. за кейс",
                        ],
                    ]:
                        embed.add_field(
                            name=elem[0],
                            value=elem[1],
                            inline=True,
                        )
                    if data[str(message.author.id)]["Rarities"] != 0:
                        for elem in data[str(message.author.id)]["Rarities"]:
                            embed.add_field(
                                name=elem[0],
                                value=urlunparse(
                                    ParseResult(
                                        "https",
                                        "cs.money",
                                        "/ru/csgo/store/",
                                        "",
                                        urlencode({"search": elem}),
                                        "",
                                    )
                                ),
                                inline=True,
                            )
                    embed.set_footer(
                        text=f"{round(float((data[str(message.author.id)]['Tiers']['Mil-Spec']/data[str(message.author.id)]['Opened'])*100), 2)}%, {round(float((data[str(message.author.id)]['Tiers']['Restricted']/data[str(message.author.id)]['Opened']))*100, 2)}%, {round(float((data[str(message.author.id)]['Tiers']['Classified']/data[str(message.author.id)]['Opened'])*100), 2)}%, {round(float((data[str(message.author.id)]['Tiers']['Covert']/data[str(message.author.id)]['Opened'])*100), 2)}%, {round(float((data[str(message.author.id)]['Tiers']['Special']/data[str(message.author.id)]['Opened'])*100), 2)}% — распределение вероятностей.\n79.19%, 15.96%, 3.66%, 0.91%, 0.31% — распределение «в идеале»."
                    )
                    await channel.send(embed=embed)

                else:
                    send_msg("Сначала открой кейс!", channel)

            elif any(elem in MesCon.lower() for elem in [" трофе"]):
                data = taisia_db["gamblerslist"].find_one()
                if re.search(r"\d+", MesCon):
                    gambler = client.get_guild(server).get_member(
                        re.search(r"\d+", MesCon).group()
                    )
                else:
                    gambler = message.author
                if str(gambler.id) in data:
                    embed = discord.Embed(
                        title=f"Трофеи {gambler.nick or gambler.name}",
                        colour=discord.Color.from_rgb(
                            randint(0, 255), randint(0, 255), randint(0, 255)
                        ),
                    )  # , description=None,
                    for i, elem in enumerate(
                        data[str(gambler.id)]["Trophies"]
                    ):
                        embed.add_field(
                            name=f"{i+1}. {elem[0]}",
                            value=f"{elem[1]} руб.",
                            inline=False,
                        )
                    # embed.set_footer(text=)
                    await channel.send(embed=embed)
                else:
                    send_msg("Сначала открой кейс!", channel)

            # печатает, когда Никита обращается
            # if message.author.id == 307789015849893888:
            #     asyncio.get_event_loop().create_task(channel.trigger_typing())

            # бочку
            elif any(
                elem in MesCon.lower()
                for elem in [
                    "сделай бочку",
                    "do a barrel roll",
                    "бочку сделай",
                ]
            ):
                send_msg(random.choice(taisia_dict["BarrelRollList"]), channel)

            elif "следи" in MesCon.lower():
                suslink = None
                if re.search(r"https://steamcommunity\.com/[^\s]+", MesCon):
                    suslink = re.search(
                        r"https://steamcommunity\.com/[^\s]+", MesCon
                    ).group(0)
                else:
                    send_msg(
                        "Жду ссылку формата `https://steamcommunity.com/...`, спасибо!",
                        channel,
                    )
                if suslink:
                    suscomm = MesCon.split(suslink, 1)[1]
                    suslist = taisia_db["suslist"].find_one()
                    if suslink not in suslist["sus"].keys():
                        new_sus = {
                            suslink: {
                                "Submitter": message.author.id,
                                "Comment": suscomm or None,
                                "Date": datetime.datetime.today().strftime(
                                    "%Y/%m/%d"
                                ),
                                "is_cheater": True
                                if (
                                    any(
                                        elem in suscomm
                                        for elem in [
                                            "хвх",
                                            "крутилк",
                                            "спинбот",
                                            "вх",
                                            "аим",
                                            "вертол",
                                            "триггер",
                                            "наводк",
                                        ]
                                    )
                                    and "не чит" not in suscomm
                                )
                                else False,
                            }
                        }
                        suslist["sus"].update(new_sus)
                        taisia_db["suslist"].update_one(
                            {"_id": suslist["_id"]},
                            {
                                "$set": {
                                    "Stat": suslist["Stat"],
                                    "sus": suslist["sus"],
                                }
                            },
                        )
                        send_msg(
                            random.choice(taisia_dict["susadded"]), channel
                        )
                    else:
                        send_msg(
                            random.choice(taisia_dict["sus_already"]), channel
                        )

            elif any(
                elem in MesCon.lower()
                for elem in ["подозреваем", "саспект", "патрул", "бан", "чит"]
            ):
                suslist = taisia_db["suslist"].find_one()
                embed = discord.Embed(
                    title=f"Ждут бана: {len(suslist['sus'])}",
                    colour=discord.Color.from_rgb(
                        randint(0, 255), randint(0, 255), randint(0, 255)
                    ),
                )

                random_sus = random.choice(
                    [
                        key
                        for key, elem in suslist["sus"].items()
                        if elem["is_cheater"]
                    ]
                )
                random_sus_days = (
                    datetime.datetime.now()
                    - datetime.datetime.strptime(
                        suslist["sus"][random_sus]["Date"], "%Y/%m/%d"
                    )
                ).days
                print(suslist["sus"][random_sus]["Submitter"])
                print(int(suslist["sus"][random_sus]["Submitter"]))
                print(client.get_guild(server).get_member(476100337355456552))
                print(
                    client.get_guild(server)
                    .get_member(int(suslist["sus"][random_sus]["Submitter"]))
                    .nick
                )
                if suslist["sus"][random_sus].get("Comment", "").strip():
                    random_sus_comm = f"\n_«{suslist['sus'][random_sus].get('Comment', '').strip()}»\n— по мнению {client.get_guild(server).get_member(int(suslist['sus'][random_sus]['Submitter'])).nick or client.get_guild(server).get_member(int(suslist['sus'][random_sus]['Submitter'])).name}_"
                else:
                    random_sus_comm = f"\n_Увы, описание подозреваемого {client.get_guild(server).get_member(int(suslist['sus'][random_sus]['Submitter'])).nick or client.get_guild(server).get_member(int(suslist['sus'][random_sus]['Submitter'])).name} не предоставил._"

                for elem in [
                    ["Забанено:", f"{suslist['Stat']['Banned']}"],
                    [
                        "Неоспоримых читеров:",
                        f"{len([None for elem in suslist['sus'].values() if elem['is_cheater']])}",
                    ],
                    [
                        "Среднее время до бана:",
                        f"{round(sum(suslist['Stat']['Wait times'])/len(suslist['Stat']['Wait times']), 1)} {chislitelnoye(int(round(sum(suslist['Stat']['Wait times'])/len(suslist['Stat']['Wait times']), 1)))}",
                    ],
                    [
                        f"...например, этот гражданин гуляет без бана {random_sus_days} {chislitelnoye(random_sus_days)}:",
                        f"{random_sus}{random_sus_comm}",
                    ],
                ]:
                    embed.add_field(
                        name=elem[0],
                        value=elem[1],
                        inline=False,
                    )
                # embed.set_footer(text=)
                await channel.send(embed=embed)

            elif any(elem in MesCon.lower() for elem in [" стат", " stat"]):
                data = taisia_db["gamblerslist"].find_one()
                totop = 0
                totsp = 0
                totearn = 0
                tottot = 0
                totluck = None
                totlose = None
                respearn = None  # responsible for % earned
                respspent = None  # responsible for % spent
                tottiers = {
                    "Mil-Spec": 0,
                    "Restricted": 0,
                    "Classified": 0,
                    "Covert": 0,
                    "Special": 0,
                }
                for user_id, stat in data.items():
                    if user_id == "_id":
                        continue
                    totop += stat["Opened"]
                    totsp += stat["Spent"]
                    totearn += stat["Earned"]
                    tottot += stat["Total"]

                    if (
                        totluck is None
                        or (stat["Total"] / stat["Opened"]) > totluck
                    ):
                        totluck = round(stat["Total"] / stat["Opened"], 2)
                        totlucker = (
                            client.get_guild(server)
                            .get_member(int(user_id))
                            .nick
                            or client.get_guild(server)
                            .get_member(int(user_id))
                            .name
                        )
                        totluckopened = stat["Opened"]
                    if (
                        totlose is None
                        or (stat["Total"] / stat["Opened"]) < totlose
                    ):
                        totlose = round(stat["Total"] / stat["Opened"], 2)
                        totloseopened = stat["Opened"]
                        totloser = (
                            client.get_guild(server)
                            .get_member(int(user_id))
                            .nick
                            or client.get_guild(server)
                            .get_member(int(user_id))
                            .name
                        )
                    if respearn is None or stat["Earned"] > respearn:
                        respearn = stat["Earned"]
                        respearn_name = (
                            client.get_guild(server)
                            .get_member(int(user_id))
                            .nick
                            or client.get_guild(server)
                            .get_member(int(user_id))
                            .name
                        )
                    if respspent is None or stat["Spent"] > respspent:
                        respspent = stat["Spent"]
                        respspent_name = (
                            client.get_guild(server)
                            .get_member(int(user_id))
                            .nick
                            or client.get_guild(server)
                            .get_member(int(user_id))
                            .name
                        )
                    for tier in tottiers:
                        tottiers[tier] += stat["Tiers"][tier]
                embed = discord.Embed(
                    title=f"Кейсов открыто: {totop}",
                    colour=discord.Color.from_rgb(
                        randint(0, 255), randint(0, 255), randint(0, 255)
                    ),
                )  # , description=None,
                for elem in [
                    ["Всего потрачено на кейсы:", round(totsp, 2)],
                    ["Заработано:", round(totearn, 2)],
                    ["Сальдо:", round(tottot, 2)],
                    ["Ножей и перчаток:", tottiers["Special"]],
                    [
                        "О, счастливчик:",
                        f"__{totlucker}__ — {totluck} руб./кейс,\nоткрыл: {totluckopened}",
                    ],
                    [
                        "Главный неудачник:",
                        f"__{totloser}__ — {totlose} руб./кейс,\nоткрыл: {totloseopened}",
                    ],
                ]:
                    embed.add_field(
                        name=elem[0],
                        value=elem[1],
                        inline=True,
                    )
                embed.set_footer(
                    text=f"{respearn_name} ответственен за {round((respearn/totearn)*100)}% всей прибыли,\n{respspent_name if respspent_name != respearn_name else 'он же'} — за {round((respspent/totsp)*100)}% всех трат."
                )
                await channel.send(embed=embed)

            elif any(
                elem in MesCon.lower() for elem in [" подтверди", " podtverdi"]
            ):
                if message.author.id == Mark:
                    send_msg(
                        random.choice(
                            ["Подтверждаю.", "Подтверждаю!", "Подтверждаю..."]
                        ),
                        channel,
                    )
                else:
                    send_msg(
                        random.choice(
                            [
                                "Подтверждаю.",
                                "Подтверждаю!",
                                "Подтверждаю...",
                                "Не могу.",
                                "Я?",
                                "Я же не пресс-секретарь!",
                                "Не могу ничего сказать по вопросу!",
                                "Не могу подтвердить",
                                "Не буду.",
                                "Подтверждаю, что это не так!",
                            ]
                        ),
                        channel,
                    )

            # капсулы
            elif any(
                elem in MesCon.lower()
                for elem in [
                    "мажор",
                    "рмр",
                    "rmr",
                    "2021",
                    "стокгольм",
                    "2020",
                ]
            ):
                if any(
                    elem in MesCon.lower()
                    for elem in ["мажор", "2021", "стокгольм"]
                ):
                    capsule_event = "Stockholm 2021"
                elif any(
                    elem in MesCon.lower() for elem in ["рмр", "rmr", "2020"]
                ):
                    capsule_event = "2020 RMR"
                if (
                    channel == client.get_channel(krtlshn)
                    or channel == client.get_channel(acdm)
                    or gamblelimit > 0
                ):
                    NumOfCaps = re.search(r"^\d | \d | \d$", MesCon)
                    if NumOfCaps is None:
                        NumOfCaps = 1
                    else:
                        NumOfCaps = int(NumOfCaps[0])
                    if NumOfCaps > 7:
                        NumOfCaps = 1
                        send_msg(
                            random.choice(taisia_dict["too_many_capsules"]),
                            channel,
                        )

                    if "лег" in MesCon.lower():
                        capsule_tier = taisia_dict[capsule_event]["Legends"]
                    elif "сопер" in MesCon.lower():
                        capsule_tier = taisia_dict[capsule_event]["Contenders"]
                    elif "претен" in MesCon.lower():
                        capsule_tier = taisia_dict[capsule_event][
                            "Challengers"
                        ]
                    else:
                        capsule_tier = random.choice(
                            list(taisia_dict[capsule_event].values())
                        )

                    if channel != client.get_channel(
                        krtlshn
                    ) and channel != client.get_channel(acdm):
                        gamblelimit -= 1
                        print("Gamble limit is down to", gamblelimit)
                    capsule_msg = []
                    for _ in range(NumOfCaps):
                        capsule_quality = random.choices(
                            [
                                ["", ":blue_circle:"],
                                [" (Holo)", ":purple_circle:"],
                                [" (Foil)", ":flamingo:"],
                                [" (Gold)", ":red_circle:"],
                            ],
                            weights=[79.81, 16.36, 3.19, 0.64],
                        )[0]
                        capsule_msg.append(
                            f"{capsule_quality[1]} Наклейка | {random.choice(capsule_tier)}{capsule_quality[0]} | {capsule_event}"
                        )
                    send_msg("\n".join(capsule_msg), channel)
                else:
                    send_msg(
                        random.choice(taisia_dict["openingwrongchannel"]),
                        channel,
                    )
                    if (
                        message.author
                        not in client.get_channel(krtlshn).members
                    ):
                        await client.get_channel(krtlshn).set_permissions(
                            message.author,
                            read_messages=True,
                            send_messages=True,
                        )
                        send_msg(
                            random.choice(taisia_dict["not_in_krtlshn"]),
                            channel,
                        )

            elif any(
                elem in MesCon.lower() for elem in ["капсул", "корон", "краун"]
            ):
                if (
                    channel == client.get_channel(krtlshn)
                    or channel == client.get_channel(acdm)
                    or gamblelimit > 0
                ):
                    NumOfCaps = re.search(r"^\d | \d | \d$", MesCon)
                    if NumOfCaps is None:
                        NumOfCaps = 1
                    else:
                        NumOfCaps = int(NumOfCaps[0])
                    if NumOfCaps > 7:
                        NumOfCaps = 1
                        send_msg(
                            random.choice(taisia_dict["too_many_capsules"]),
                            channel,
                        )

                    if channel != client.get_channel(
                        krtlshn
                    ) and channel != client.get_channel(acdm):
                        gamblelimit -= 1
                        print("Gamble limit is down to", gamblelimit)
                    capsule_msg = []
                    for _ in range(NumOfCaps):
                        capsule_quality = random.choices(
                            [
                                ["High Grade", "", ":blue_circle:"],
                                ["Remarkable", " (Holo)", ":purple_circle:"],
                                ["Exotic", " (Foil)", ":flamingo:"],
                            ],
                            weights=[80, 15, 5],
                        )
                        dropped_sticker = random.choice(
                            list(
                                taisia_dict["Sticker Capsule 2"][
                                    capsule_quality[0][0]
                                ]
                            )
                        )
                        if dropped_sticker == "Crown":
                            capsule_emoji = ":crown:"
                        else:
                            capsule_emoji = capsule_quality[0][2]
                        capsule_msg.append(
                            f"{capsule_emoji} Sticker | {dropped_sticker}{capsule_quality[0][1]}"
                        )
                    send_msg("\n".join(capsule_msg), channel)
                else:
                    send_msg(
                        random.choice(taisia_dict["openingwrongchannel"]),
                        channel,
                    )
                    if (
                        message.author
                        not in client.get_channel(krtlshn).members
                    ):
                        await client.get_channel(krtlshn).set_permissions(
                            message.author,
                            read_messages=True,
                            send_messages=True,
                        )
                        send_msg(
                            random.choice(taisia_dict["not_in_krtlshn"]),
                            channel,
                        )

            # анекдоты категории Б
            elif " анек" in MesCon.lower():
                if randint(0, 1):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            "https://baneks.ru/random"
                        ) as response:
                            html = await response.read()
                            html = html.decode("utf8", errors="ignore")
                            anec = re.search(
                                r"<p>.*</p>", html, flags=re.DOTALL
                            )
                            anec = re.sub(r"<[^<]*>", "", anec[0]).strip()
                            send_msg(
                                f"«{anec}»\n\n{random.choice(taisia_dict['AnecdoteList'])}",
                                channel,
                            )
                else:
                    global banek_count
                    banek_vk = requests.get(
                        "https://api.vk.com/method/wall.get",
                        params={
                            "owner_id": -85443458,
                            "count": 1,
                            "offset": randint(0, banek_count),
                            "access_token": settings.access_token,
                            "v": "5.84",
                        },
                    )
                    banek = banek_vk.json()
                    banek_count = banek["response"]["count"]
                    if len(banek["response"]["items"][0]["text"]) > 2000:
                        send_msg(
                            f"{random.choice(taisia_dict['2000_anek'])}\n\n{random.choice(taisia_dict['long_anek_link'])}||vk.com/wall{banek['response']['items'][0]['from_id']}_{banek['response']['items'][0]['id']}||",
                            channel,
                        )
                    else:
                        send_msg(
                            f"«{banek['response']['items'][0]['text']}»\n\n{random.choice(taisia_dict['AnecdoteList'])}",
                            channel,
                        )

            # наш ответ рандомботу
            elif any(
                elem in MesCon.lower()
                for elem in ["choose", "выбери", "выбор"]
            ):
                await Chooser("choose", channel, MesCon)
            elif " цвет" in MesCon.lower() and any(
                elem in MesCon.lower()
                for elem in [" любой", " случайн", " рандом"]
            ):
                await Chooser("colour", channel, MesCon)
            elif any(
                elem in MesCon.lower()
                for elem in [" да или нет", " нет или да"]
            ):
                await Chooser("yesorno", channel, MesCon)

            # выбор карты
            elif (
                any(elem in MesCon.lower() for elem in ["карт", "голос"])
                and message.author.voice
            ):
                global vc
                global EndEvent
                print("play")
                vc = await message.author.voice.channel.connect()
                vc.play(
                    discord.FFmpegPCMAudio(
                        executable=settings.ffmpeg_path,
                        source=os.path.join(
                            settings.music_files_folder, "VoteStart.mp3"
                        ),
                    )
                )
                vc.source = discord.PCMVolumeTransformer(vc.source, volume=0.2)

                msg_votemap_cont = f"{random.choice(taisia_dict['GreetList'])}\n\n{random.choice(taisia_dict['Left2VoteList'])}"
                for member in (
                    client.get_guild(server)
                    .get_member(Taechka)
                    .voice.channel.members
                ):
                    if not member.bot:
                        msg_votemap_cont += f"<@!{member.id}> "

                msg_votemap = await channel.send(msg_votemap_cont)

                global votes
                votes[msg_votemap.id] = {
                    "players": set(),
                    "maps": [],
                }

                # баны
                if "бан" in MesCon.lower():
                    map_bans_msg = await channel.send(
                        random.choice(taisia_dict["map_bans_list"])
                    )
                    await msg_votemap.edit(
                        content=msg_votemap.content
                        + "\n\n"
                        + random.choice(taisia_dict["awaiting_banned_maps"])
                    )

                for emoji in taisia_dict["MapsEmoji"]:
                    await msg_votemap.add_reaction(emoji)
                await EndEvent.wait()
                await channel.send(votemap_random(msg_votemap))

                # Назидание от Саши Симпла
                if not randint(0, 3):
                    included_extensions = ["jpg", "jpeg", "bmp", "png", "gif"]
                    simpics = [
                        fn
                        for fn in os.listdir(settings.simp_files_folder)
                        if any(fn.endswith(ext) for ext in included_extensions)
                    ]
                    with open(
                        os.path.join(
                            settings.simp_files_folder, random.choice(simpics)
                        ),
                        "rb",
                    ) as f:
                        simpic = discord.File(f)
                    await channel.send(
                        content=random.choice(taisia_dict["simpicList"]),
                        file=simpic,
                    )

                if vc:
                    while vc.is_playing():
                        await asyncio.sleep(1)
                    await vc.disconnect()

                EndEvent.clear()

            # напоминание посмотреть демку
            elif re.match(r".*\d+\-\d+", MesCon):
                # if [
                #     member
                #     for member in client.get_guild(server).members
                #     if member.activity
                #     and "Counter-Strike: Global Offensive" == member.activity.name
                # ]:
                roundcount = [
                    int(n) for n in re.findall(r"(\d+)\-(\d+)", MesCon)[0]
                ]
                roundnumber = sum(roundcount) + 1
                AvgRndTime = 95
                if roundnumber < 32:
                    if "турбо" in MesCon:
                        if sum(roundcount) > 12:
                            AvgRndNmbr = 16
                        else:
                            AvgRndNmbr = 14
                    else:
                        if sum(roundcount) > 23:
                            AvgRndNmbr = 30
                        else:
                            AvgRndNmbr = 26
                    roundtrouble = re.sub(
                        r"\d+\-\d+\s*", "", MesCon.split(" ", 1)[1]
                    ) or random.choice(taisia_dict["demo_reason_list"])
                    roundtrouble = roundtrouble.replace("турбо", "")
                    if " я " in roundtrouble:
                        roundtrouble = roundtrouble.replace(" я ", " он ")
                    roundtrouble = roundtrouble.strip()
                    asyncio.get_event_loop().call_later(
                        ((AvgRndNmbr - roundnumber) * AvgRndTime),
                        send_msg,
                        f"Пересмотрите {roundnumber}-й раунд, счёт {roundcount[0]}-{roundcount[1]}. <@!{message.author.id}> говорит, там {roundtrouble}.",
                        channel,
                    )

            # kill
            elif "кыш" in MesCon.lower():
                if message.author.id == Mark:
                    PrintCurrTime("\n> > >Left at")
                    if vc:
                        await vc.disconnect()
                    exit()
                else:
                    send_msg(
                        random.choice(taisia_dict["will_not_exit"]), channel
                    )

        # О Т К Р Ы Т И Е   К Е Й С О В #не в колл ми бай йор нейм чтобы при уточнении кейса не писать обращение
        if (
            MesCon.startswith(taisia_dict["TaisiaName"])
            and " кейс" in MesCon.lower()
            or (ExpectingCaseName and message.author == UserExpectingCase)
        ):
            if (
                channel == client.get_channel(krtlshn)
                or channel == client.get_channel(acdm)
                or gamblelimit > 0
            ):
                if caserollin:
                    send_msg(
                        random.choice(taisia_dict["caserollinList"]), channel
                    )
                else:
                    caseweights = [79.19, 15.96, 3.66, 0.91, 0.31]
                    old_cases = [
                        "Revolver Case",
                        "Operation Phoenix Weapon Case",
                        "Operation Vanguard Weapon Case",
                        "CS:GO Weapon Case",
                        "CS:GO Weapon Case 2",
                        "CS:GO Weapon Case 3",
                        "Operation Bravo Case",
                        "eSports 2013 Case",
                        "Winter Offensive Weapon Case",
                        "eSports 2013 Winter Case",
                        "eSports 2014 Summer Case",
                    ]
                    exceptional_knife_cases = taisia_dict["ExceptionalCases"][
                        0
                    ]
                    exceptional_glove_cases = taisia_dict["ExceptionalCases"][
                        1
                    ]
                    caseopeningtier = [
                        ["Mil-Spec", 0x4B69FF, ":blue_circle:"],
                        ["Restricted", 0x8847FF, ":purple_circle:"],
                        ["Classified", 0xD32CE6, ":flamingo:"],
                        ["Covert", 0xEB4B4B, ":red_circle:"],
                        ["Special", 0xFFD700, ":yellow_circle:"],
                    ]
                    casename = None
                    UserExpectingCase = None
                    steam_api_err = False
                    marketplaceprice = None
                    caseprofit = 0

                    for currcasename in taisia_dict["Cases"]:
                        if any(
                            elem in MesCon.lower()
                            for elem in taisia_dict["Cases"][currcasename][
                                "Aliases"
                            ]
                        ):
                            casename = currcasename
                            break

                    if casename is None:
                        if channel.id == krtlshn:
                            ExpectingCaseName = True
                            UserExpectingCase = message.author
                            case_list = await client.get_channel(
                                krtlshn
                            ).fetch_message(announcement_message)
                            await case_list.reply(
                                random.choice(taisia_dict["NoCaseNameList"]),
                                mention_author=True,
                            )
                            await asyncio.sleep(15)
                            ExpectingCaseName = False

                    casedropstattrak = ""
                    casedropstar = ""
                    cdiparameter = ""

                    if (
                        message.author.voice
                        and client.get_guild(server).get_member(Taechka)
                        not in message.author.voice.channel.members
                        and not randint(0, 4)
                    ):
                        vc = await message.author.voice.channel.connect()
                        vc.play(
                            discord.FFmpegPCMAudio(
                                executable=settings.ffmpeg_path,
                                source=os.path.join(
                                    settings.music_files_folder, "OpenCase.mp3"
                                ),
                            )
                        )
                        vc.source = discord.PCMVolumeTransformer(
                            vc.source, volume=0.2
                        )

                    def CaseQualityCheck(flt):  # изношенность по флоату
                        casedropqualities = [
                            ["Factory New", 0.07],
                            ["Minimal Wear", 0.15],
                            ["Field-Tested", 0.37],
                            ["Well-Worn", 0.44],
                            ["Battle-Scarred", 1],
                        ]
                        for i in range(5):
                            if flt < casedropqualities[i][1]:
                                return casedropqualities[i][0]

                    DropEstimation = {
                        "Mil-Spec": {
                            True: "Ok",
                            False: "Bad",
                        },
                        "Restricted": {
                            True: "Good",
                            False: "Bad",
                        },
                        "Classified": {
                            True: "Best",
                            False: "Good",
                        },
                        "Covert": {
                            True: "Crazy",
                            False: "Best",
                        },
                        "Special": {True: "Crazy", False: "Crazy"},
                    }

                    # если таки выбран кейс
                    if casename:
                        if channel != client.get_channel(
                            krtlshn
                        ) and channel != client.get_channel(acdm):
                            gamblelimit -= 1
                            print("Gamble limit is down to ", gamblelimit)
                        casedropitem = None
                        casedropfloat = -1
                        caserollin = True
                        casedroptier = random.choices(
                            caseopeningtier, weights=caseweights
                        )[0]
                        if casedroptier[0] == "Special":
                            casedropstar = "★ "

                            for elem in exceptional_knife_cases:
                                if casename in elem[0]:
                                    casedropitem = random.choice(
                                        list(taisia_dict[elem[1]].keys())
                                    )
                                    casedropfloat = random.uniform(
                                        taisia_dict[elem[1]][casedropitem][
                                            "floatrange"
                                        ][0],
                                        taisia_dict[elem[1]][casedropitem][
                                            "floatrange"
                                        ][1],
                                    )
                                    if casedropfloat == 1:
                                        casedropfloat -= 0.00001
                                    break

                            if not casedropitem:
                                for elem in exceptional_glove_cases:
                                    if casename in elem[0]:
                                        casedropitem = random.choice(
                                            taisia_dict["Gloves"][elem[1]]
                                        )
                                        casedropfloat = random.uniform(
                                            0.06, 0.8
                                        )
                                        break

                            if not casedropitem:
                                if any(elem in casename for elem in old_cases):
                                    casedropitem = random.choice(
                                        list(taisia_dict["Knives"].keys())
                                    )
                                    casedropfloat = random.uniform(
                                        taisia_dict["Knives"][casedropitem][
                                            "floatrange"
                                        ][0],
                                        taisia_dict["Knives"][casedropitem][
                                            "floatrange"
                                        ][1],
                                    )
                                    if casedropfloat == 1:
                                        casedropfloat -= 0.00001
                                else:
                                    casedropitem = random.choice(
                                        list(
                                            taisia_dict["Cases"][casename][
                                                casedroptier[0]
                                            ].keys()
                                        )
                                    )
                                    casedropfloat = random.uniform(
                                        taisia_dict["Cases"][casename][
                                            casedroptier[0]
                                        ][casedropitem]["floatrange"][0],
                                        taisia_dict["Cases"][casename][
                                            casedroptier[0]
                                        ][casedropitem]["floatrange"][1],
                                    )
                                    if casedropfloat == 1:
                                        casedropfloat -= 0.0001

                        else:
                            casedropitem = random.choice(
                                list(
                                    taisia_dict["Cases"][casename][
                                        casedroptier[0]
                                    ].keys()
                                )
                            )
                            casedropfloat = random.uniform(
                                taisia_dict["Cases"][casename][
                                    casedroptier[0]
                                ][casedropitem]["floatrange"][0],
                                taisia_dict["Cases"][casename][
                                    casedroptier[0]
                                ][casedropitem]["floatrange"][1],
                            )
                            if casedropfloat == 1:
                                casedropfloat -= 0.0001

                        # casedropitem = "M9 Bayonet | Gamma Doppler"
                        # casedroptier[0] = "Special"

                        if "moonrise" in casedropitem.lower() and not randint(
                            0, 99
                        ):  # case drop item parameter
                            cdiparameter = "Star Pattern"
                        elif "seasons" in casedropitem.lower() and not randint(
                            0, 49
                        ):
                            cdiparameter = "Blue Leaf Pattern"
                        elif (
                            "fade" in casedropitem.lower()
                            and "gloves" not in casedropitem.lower()
                            and "marble" not in casedropitem.lower()
                        ):
                            cdiparameter = f"Fade: {randint(80, 100)}%"
                        elif (
                            "case hardened" in casedropitem.lower()
                            and "gloves" not in casedropitem.lower()
                        ):
                            if not randint(0, 99):
                                cdiparameter = "Blue Gem"
                        elif (
                            "marble fade" in casedropitem.lower()
                            and not randint(0, 99)
                            and any(
                                elem in casedropitem.lower()
                                for elem in [
                                    "karambit",
                                    "bayonet",
                                    "flip",
                                    "gut",
                                ]
                            )
                        ):
                            cdiparameter = "Fire and Ice"
                        elif "gamma doppler" in casedropitem.lower():
                            cdiparameter = random.choices(
                                [
                                    "Phase 1",
                                    "Phase 2",
                                    "Phase 3",
                                    "Phase 4",
                                    "Emerald",
                                ],
                                weights=[22.5, 22.5, 22.5, 22.5, 10],
                            )[0]
                        elif "doppler" in casedropitem.lower():
                            cdiparameter = random.choices(
                                [
                                    "Phase 1",
                                    "Phase 2",
                                    "Phase 3",
                                    "Phase 4",
                                    "Sapphire",
                                    "Ruby",
                                    "Black Pearl",
                                ],
                                weights=[22.5, 22.5, 22.5, 22.5, 4.5, 4.5, 1],
                            )[0]

                        if (
                            not randint(0, 9)
                            and "gloves" not in casedropitem.lower()
                            and "wraps" not in casedropitem.lower()
                        ):
                            casedropstattrak = "StatTrak™ "
                        casedropquality = CaseQualityCheck(casedropfloat)
                        casedropest = DropEstimation[casedroptier[0]][
                            bool(casedropstattrak)
                        ]
                        casedropurl = f"https://steamcommunity.com/market/listings/730/{casedropstar}{casedropstattrak}{casedropitem} ({casedropquality})".replace(
                            " ", "%20"
                        )
                        embed = discord.Embed(
                            title=random.choice(
                                taisia_dict["GambleReactions"][casedropest]
                            ),
                            colour=discord.Color((casedroptier[1])),
                            url=casedropurl,
                        )
                        embed.add_field(
                            name=f"{casedropstar}{casedropstattrak}{casedropitem}",
                            value=casedroptier[0],
                        )
                        embed.add_field(
                            name=casedropquality,
                            value=CaseTrunc(casedropfloat, 1000000),
                        )
                        if cdiparameter:
                            embed.add_field(
                                name=":cherries:", value=cdiparameter
                            )

                        if casedroptier[0] == "Special":
                            for elem in exceptional_knife_cases:
                                if casename in elem[0]:
                                    embed.set_footer(
                                        text=taisia_dict[elem[1]][
                                            casedropitem
                                        ]["text"]
                                    )
                                    break

                            if any(
                                elem in casename
                                for elem in [
                                    "Snakebite Case",
                                    "Operation Broken Fang Case",
                                    "Clutch Case",
                                    "Operation Hydra Case",
                                    "Glove Case",
                                    "Recoil Case",
                                ]
                            ):
                                embed.set_footer(
                                    text=random.choice(
                                        taisia_dict["GlovesReactionList"]
                                    )
                                )

                            elif any(elem in casename for elem in old_cases):
                                embed.set_footer(
                                    text=taisia_dict["Knives"][casedropitem][
                                        "text"
                                    ]
                                )
                            elif not embed.footer:
                                embed.set_footer(
                                    text=taisia_dict["Cases"][casename][
                                        "Special"
                                    ][casedropitem]["text"]
                                )
                        else:
                            embed.set_footer(
                                text=taisia_dict["Cases"][casename][
                                    casedroptier[0]
                                ][casedropitem]["text"]
                            )

                        # else:
                        #     print(itemurl, caseurl)
                        #     embed.add_field(name="Габела!", value=f"Какие-то проблемы с API Стима. Не ответили где-то тут: {itemurl} ; {caseurl}")
                        # позиция, на котором выигрыш
                        winplace = randint(4, 15)
                        polyana = ""  # прокрутка в виде строки
                        for i in range(
                            7
                        ):  # изначальное поле, которое отсылается
                            randomitem = ""
                            randomitemtier = random.choices(
                                caseopeningtier, weights=caseweights
                            )[0]
                            rollstt = ""  # статтрек
                            randomdropstar = ""
                            if randomitemtier[0] == "Special":
                                randomdropstar = "★ "
                                for elem in exceptional_knife_cases:
                                    if casename in elem[0]:
                                        randomitem = random.choice(
                                            list(taisia_dict[elem[1]].keys())
                                        )
                                        break

                                if not randomitem:
                                    for elem in exceptional_glove_cases:
                                        if casename in elem[0]:
                                            randomitem = random.choice(
                                                taisia_dict["Gloves"][elem[1]]
                                            )
                                            break

                                if not randomitem:
                                    if any(
                                        elem in casename for elem in old_cases
                                    ):
                                        randomitem = random.choice(
                                            list(taisia_dict["Knives"].keys())
                                        )
                                    else:
                                        randomitem = random.choice(
                                            list(
                                                taisia_dict["Cases"][casename][
                                                    "Special"
                                                ].keys()
                                            )
                                        )
                            else:
                                randomitem = random.choice(
                                    list(
                                        taisia_dict["Cases"][casename][
                                            randomitemtier[0]
                                        ].keys()
                                    )
                                )
                            if (
                                not randint(0, 9)
                                and "gloves" not in randomitem.lower()
                                and "wraps" not in randomitem.lower()
                            ):
                                rollstt = "StatTrak™ "
                            randomitem_marketplaceprice_final = ""
                            if i != 3:
                                polyana = (
                                    polyana
                                    + f"\n{randomitemtier[2]} {randomdropstar}{rollstt}{randomitem}{randomitem_marketplaceprice_final}"
                                )
                            else:  # подчёркивает четвёртый предмет
                                polyana = (
                                    polyana
                                    + f"\n{randomitemtier[2]} **{randomdropstar}{rollstt}{randomitem}{randomitem_marketplaceprice_final}**"
                                )

                        polyanaroll = await channel.send(polyana)

                        # чтобы не было видно края
                        for i in range(winplace + 3):
                            rollstt = ""
                            randomdropstar = ""
                            randomitem = ""
                            polyana = polyanaroll.content
                            randomitemtier = random.choices(
                                caseopeningtier,
                                weights=caseweights,
                            )[0]
                            if randomitemtier[0] == "Special":
                                randomdropstar = "★ "
                                for elem in exceptional_knife_cases:
                                    if casename in elem[0]:
                                        randomitem = random.choice(
                                            list(taisia_dict[elem[1]].keys())
                                        )
                                        break

                                if not randomitem:
                                    for elem in exceptional_glove_cases:
                                        if casename in elem[0]:
                                            randomitem = random.choice(
                                                taisia_dict["Gloves"][elem[1]]
                                            )
                                            break

                                if not randomitem:
                                    if any(
                                        elem in casename for elem in old_cases
                                    ):
                                        randomitem = random.choice(
                                            list(taisia_dict["Knives"].keys())
                                        )
                                    else:
                                        randomitem = random.choice(
                                            list(
                                                taisia_dict["Cases"][casename][
                                                    randomitemtier[0]
                                                ].keys()
                                            )
                                        )
                            else:
                                randomitem = random.choice(
                                    list(
                                        taisia_dict["Cases"][casename][
                                            randomitemtier[0]
                                        ].keys()
                                    )
                                )

                            if (
                                not randint(0, 9)
                                and "gloves" not in randomitem.lower()
                                and "wraps" not in randomitem.lower()
                            ):
                                rollstt = "StatTrak™ "

                            if (
                                i == winplace - 1
                            ):  # если сейчас на экране должен появиться выигрыш, он подставляется вместо случайного предмета
                                polyana = (
                                    "\n"
                                    + replacenth(  # с прошлой убираются все звёздочки, но после 4 и до 5 переноса строки добавляются
                                        replacenth(
                                            re.sub(
                                                r"^.*\n", "", polyana
                                            ).replace("**", "")
                                            + f"\n{casedroptier[2]} {casedropstar}{casedropstattrak}{casedropitem}\n",
                                            "\n",
                                            "\n**",
                                            3,
                                        ),
                                        "\n",
                                        "**\n",
                                        4,
                                    )
                                )
                            else:
                                polyana = "\n" + replacenth(
                                    replacenth(
                                        re.sub(r"^.*\n", "", polyana).replace(
                                            "**", ""
                                        )
                                        + f"\n{randomitemtier[2]} {randomdropstar}{rollstt}{randomitem}\n",
                                        "\n",
                                        "\n**",
                                        3,
                                    ),
                                    "\n",
                                    "**\n",
                                    4,
                                )

                            await asyncio.sleep(1)
                            if vc:
                                while vc.is_playing():
                                    await asyncio.sleep(1)
                                await vc.disconnect()
                            await polyanaroll.edit(content=polyana)

                        # экономический аспект
                        # casedropitem = "Butterfly Knife | Fade"
                        # casedropquality = "Factory New"
                        if "|" not in casedropitem:
                            casedropquality = ""
                        else:
                            casedropquality = f"({casedropquality})"
                        markethashname = f"{casedropstar}{casedropstattrak}{casedropitem} {casedropquality}"

                        caseurl = urlunparse(
                            ParseResult(
                                "https",
                                "steamcommunity.com",
                                "/market/priceoverview/",
                                "",
                                urlencode(
                                    {
                                        "market_hash_name": casename,
                                        "currency": 5,
                                        "appid": 730,
                                    }
                                ),
                                "",
                            )
                        )
                        itemurl = urlunparse(
                            ParseResult(
                                "https",
                                "steamcommunity.com",
                                "/market/priceoverview/",
                                "",
                                urlencode(
                                    {
                                        "market_hash_name": markethashname,
                                        "currency": 5,
                                        "appid": 730,
                                    }
                                ),
                                "",
                            )
                        )
                        caseexpense = 0
                        if requests.get(caseurl).json().get("success"):
                            caseexpense = (
                                float(
                                    (
                                        (requests.get(caseurl)).json()[
                                            "lowest_price"
                                        ]
                                    )
                                    .split(" ", 1)[0]
                                    .replace(",", ".")
                                )
                                + case_key_price  # стоимость ключа
                            )
                        else:
                            steam_api_err = True

                        if requests.get(itemurl).json().get("success"):
                            marketplaceprice = float(
                                (
                                    (requests.get(itemurl))
                                    .json()
                                    .get("lowest_price", "0")
                                )
                                .split(" ", 1)[0]
                                .replace(",", ".")
                            )
                        else:
                            steam_api_err = True

                        # if not steam_api_err:
                        if marketplaceprice:
                            caseprofit = marketplaceprice - caseexpense
                            if caseprofit > 0:
                                profitemoji = ":white_check_mark:"
                            else:
                                profitemoji = ":x:"
                            embed.add_field(
                                name="Прибыль:",
                                value=f"{profitemoji} {caseprofit:8.2f} руб.",
                                inline=True,
                            )
                            embed.add_field(
                                name="Доход:",
                                value=f"{marketplaceprice:8.2f} руб.",
                                inline=True,
                            )
                        else:
                            csmoneyurl = urlunparse(
                                ParseResult(
                                    "https",
                                    "cs.money",
                                    "/ru/csgo/store/",
                                    "",
                                    urlencode(
                                        {
                                            "search": f"{casedropstattrak}{casedropitem} {casedropquality}"
                                        }
                                    ),
                                    "",
                                )
                            )
                            embed.add_field(
                                name=":warning:",
                                value=f"Видимо, это настолько дорогой предмет, что его нет в Стиме. {csmoneyurl}",
                                inline=True,
                            )

                        embed.add_field(
                            name="Затраты:",
                            value=f"{caseexpense:8.2f} руб.",
                            inline=True,
                        )

                        # учёт
                        # if not steam_api_err:
                        if channel != client.get_channel(acdm):
                            data = taisia_db["gamblerslist"].find_one()
                            if str(message.author.id) not in data:
                                new_gambler = {
                                    str(message.author.id): {
                                        "Opened": 0,
                                        "Earned": 0,
                                        "Spent": 0,
                                        "Total": 0,
                                        "Trophies": [
                                            ["", 0],
                                            ["", 0],
                                            ["", 0],
                                            ["", 0],
                                            ["", 0],
                                        ],
                                        "Rarities": [],
                                        "Tiers": {
                                            "Mil-Spec": 0,
                                            "Restricted": 0,
                                            "Classified": 0,
                                            "Covert": 0,
                                            "Special": 0,
                                        },
                                    }
                                }
                                data.update(new_gambler)
                            data_additions = [
                                ["Opened", 1],
                                ["Earned", marketplaceprice],
                                ["Spent", caseexpense],
                                ["Total", caseprofit],
                            ]
                            for i in range(len(data_additions)):
                                data[str(message.author.id)][
                                    data_additions[i][0]
                                ] += data_additions[i][1]
                            for elem in data[str(message.author.id)][
                                "Tiers"
                            ].keys():
                                if elem == casedroptier[0]:
                                    data[str(message.author.id)]["Tiers"][
                                        elem
                                    ] += 1
                            if marketplaceprice:
                                for i in range(0, 5):
                                    if (
                                        marketplaceprice
                                        > data[str(message.author.id)][
                                            "Trophies"
                                        ][i][1]
                                    ):
                                        data[str(message.author.id)][
                                            "Trophies"
                                        ].insert(
                                            i,
                                            [
                                                f"{casedroptier[2]} {casedropstattrak}{casedropitem} {casedropquality} {cdiparameter}",
                                                marketplaceprice,
                                            ],
                                        )
                                        data[str(message.author.id)][
                                            "Trophies"
                                        ] = data[str(message.author.id)][
                                            "Trophies"
                                        ][
                                            :5
                                        ]
                                        break
                            else:
                                data[str(message.author.id)][
                                    "Rarities"
                                ].append(
                                    [
                                        f"{casedropstattrak}{casedropitem} {casedropquality} {cdiparameter}"
                                    ]
                                )

                            taisia_db["gamblerslist"].update_one(
                                {"_id": data["_id"]},
                                {
                                    "$set": {
                                        k: value for k, value in data.items()
                                    }
                                },
                            )

                        # картинка
                        if marketplaceprice:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(
                                    casedropurl
                                ) as response:
                                    html = await response.read()
                                    html = html.decode("utf8", errors="ignore")
                                    embed.set_thumbnail(
                                        url=re.search(
                                            "%s(.*)%s"
                                            % (
                                                re.escape("https://"),
                                                re.escape("360fx360f"),
                                            ),
                                            html,
                                        ).group(0)
                                    )

                        result_embed = await channel.send(
                            embed=embed
                        )  # , reference=polyanaroll)
                        caserollin = False
                        steam_api_err = False
                        if (
                            casedroptier[0] == "Special"
                            and channel.id == krtlshn
                        ):
                            await result_embed.pin()
            else:
                send_msg(
                    random.choice(taisia_dict["openingwrongchannel"]), channel
                )
                if message.author not in client.get_channel(krtlshn).members:
                    await client.get_channel(krtlshn).set_permissions(
                        message.author, read_messages=True, send_messages=True
                    )
                    send_msg(
                        random.choice(taisia_dict["not_in_krtlshn"]), channel
                    )

        elif any(
            elem in MesCon.lower() for elem in ["спасиб", "благодар"]
        ) and any(elem in MesCon for elem in ["Тая", "Тае", "Тай", "Таю"]):
            send_msg(random.choice(taisia_dict["thanks_list"]), channel)
    except Exception as exc:
        print("err", exc)
        traceback.print_exc()


client.run(settings.token)
