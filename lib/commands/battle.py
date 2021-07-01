﻿import asyncio
import discord
import math
from threading import Thread
from discord.ext import commands
from lib.settings import *


checker = ["❎", "✅"]


async def delete(message, warning):
    await asyncio.sleep(3)
    await message.delete()
    await warning.delete()


@bot.command()
async def battle(cmd, mem: discord.Member = None):
    if mem == None or mem == cmd.author or mem.bot:
        await cmd.send("Please specify a valid opponent.")
    else:
        message = await cmd.send(f"<@!{mem.id}> Do you accept <@!{cmd.author.id}>'s challenge?")
        for emoji in checker:
            await message.add_reaction(emoji)


        def check(reaction, user):
            return user == mem and str(reaction) in checker


        try:
            reaction, user = await bot.wait_for("reaction_add", check = check, timeout = 60.0)
        except:
            await message.delete()
            await cmd.send(f"<@!{mem.id}> didn't respond to the battle challenge. Request timed out.")
            return
        await message.delete()
        choice = checker.index(str(reaction))
        if choice == 0:
            await cmd.send(f"<@!{mem.id}> refused to have a duel. What a noob!")
        elif choice == 1:
            cur.execute("SELECT * FROM economy;")
            lst = cur.fetchall()
            id_lst = [str(cmd.author.id), str(mem.id)]
            info = {}
            for data in lst:
                if data[0] in id_lst:
                    info[id_lst.index(data[0])] = data
                    if sum(data[5:57]) == 0:
                        await cmd.send("Both players must have at least 1 pet to perform battle.")
                        return
                    continue
            await cmd.send(f"<@!{mem.id}> accepted the challenge.\nChoose at most 3 pets to battle by entering `select <id> <id> <id>`.\nEg. `select 2 43 13`, `select 0 14`")
            pending = [True, True]
            _team = {}
            class Team:
                def __init__(self, user, pet, lv, hp, atk):
                    self.user = user
                    self.pet = pet
                    self.lv = lv
                    self.hp = hp
                    self.atk = atk
                    self.hp_max = hp.copy()


            def select(message):
                return message.content.startswith("select") and str(message.author.id) in id_lst and message.channel.id == cmd.message.channel.id


            while pending[0] or pending[1]:
                message = await bot.wait_for("message", check = select)
                p = id_lst.index(str(message.author.id))
                if not pending[p]:
                    await cmd.send(f"<@!{message.author.id}>, you have completed selecting!")
                    continue
                choice = message.content.split(" ")[1:]
                choices = []
                for i in choice:
                    try:
                        i = int(i)
                        choices.append(i)
                    except:
                        continue
                player_team = []
                choice = []
                for i in choices:
                    if i < 0 or i > 51:
                        continue
                    c = info[p][i + 5]
                    if c > 0:
                        choice.append(i)
                        player_team.append(c)
                n = len(player_team)
                _lv = []
                hp = []
                atk = []
                if n == 0 or n > 3:
                    await cmd.send("Please perform a valid selection.")
                    continue
                else:
                    em = discord.Embed(title=f"{message.author} has completed selecting!",
                                       color=0x2ECC71)
                    for i in range(n):
                        pet = petimg[choice[i]]
                        cons = player_team[i]
                        lv = 1 + int((-1 + math.sqrt(1 + 2 * cons)) / 2)
                        stat = stats(choice[i], lv)
                        _lv.append(lv)
                        hp.append(stat.hp)
                        atk.append(stat.atk)
                        em.add_field(name=f"{pet} Lv.`{lv}`", value=f"HP `{stat.hp}` ATK `{stat.atk}`")
                    _team[str(message.author.id)] = Team(message.author, choice, _lv, hp, atk)
                    await cmd.send(embed=em)
                    pending[p] = False
            em = discord.Embed(title="Battle Status", description="Ongoing battle", color=0x2ECC71)
            for i in id_lst:
                n = len(_team[i].pet)
                team = _team[i]
                value = "\n".join(f"`{j+1}`{petimg[team.pet[j]]} Lv.`{team.lv[j]}` HP `{team.hp[j]}/{team.hp[j]}`" for j in range(n))
                em.add_field(name=f"{team.user}'s team", value=value)
            em.set_footer(text = f"Turn {cmd.author}")
            msg = await cmd.send(embed = em)
            await cmd.send("Use `attack <your pet's position> <opponent's pet position>` to attack.\nEg. `attack 1 3`, `attack 2 1`")
            ongoing = True


            def attack_check(message):
                return str(message.author.id) in id_lst and message.content.startswith("attack")


            turn = 1
            while ongoing:
                for i in range(2):
                    message = await bot.wait_for("message", check = attack_check)
                    while not id_lst.index(str(message.author.id)) == i:
                        warning = await cmd.send(f"Chillax <@!{message.author.id}>, it's not your turn yet!")
                        thread = Thread(target = await delete(message, warning))
                        thread.start()
                        message = await bot.wait_for("message", check = attack_check)
                    try:
                        attacker, target = message.content.split(" ")[1:]
                        attacker = int(attacker) - 1
                        target = int(target) - 1
                        if attacker < 0 or target < 0:
                            raise ValueError
                        atk = _team[id_lst[i]].atk[attacker]
                        if _team[id_lst[i]].hp[attacker] == 0:
                            warning = await cmd.send(f"Invalid attack (attacker isn't alive). <@!{message.author.id}> lost this turn.")
                            thread = Thread(target = await delete(message, warning))
                            thread.start()
                            continue
                        _team[id_lst[1-i]].hp[target] -= atk
                        em = discord.Embed(title="Battle Status", description="Ongoing battle", color=0x2ECC71)
                        if _team[id_lst[1-i]].hp[target] <= 0:
                            _team[id_lst[1-i]].hp[target] = 0
                            if sum(_team[id_lst[1-i]].hp) == 0:
                                em = discord.Embed(title="Battle Status", description=f"**{_team[id_lst[i]].user}** won!", color=0x2ECC71)
                                cur.execute(f"""
                                UPDATE economy
                                SET win = win + 1, total = total + 1
                                WHERE id = '{id_lst[i]}';
                                """)
                                cur.execute(f"""
                                UPDATE economy
                                SET total = total + 1
                                WHERE id = '{id_lst[1-i]}';
                                """)
                                conn.commit()
                                await cmd.send(f"<@!{id_lst[i]}> won!")
                                await message.delete()
                                ongoing = False
                        for k in id_lst:
                            n = len(_team[k].pet)
                            team = _team[k]
                            value = "\n".join(f"`{j+1}`{petimg[team.pet[j]]} Lv.`{team.lv[j]}` HP `{team.hp[j]}/{team.hp_max[j]}`" for j in range(n))
                            em.add_field(name=f"{team.user}'s team", value=value)
                        em.set_footer(text = f"Turn {_team[id_lst[1-i]].user}")
                        await msg.edit(embed = em)
                    except:
                        warning = await cmd.send(f"Invalid attack (argument error). <@!{message.author.id}> lost this turn.")
                        thread = Thread(target = await delete(message, warning))
                        thread.start()
                        continue
                    await message.delete()


@battle.error
async def battle_error(cmd, error):
    if isinstance(error, commands.UserInputError):
        await cmd.send("Please check your input again.")
