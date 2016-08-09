import datetime
import discord
from discord.ext import commands
import asyncio
import json
import ujson
import re

description = '''
            A Bot to provide Basic Quoting functionality for Discord
            '''

bot = commands.Bot(command_prefix='!', description=description)

@bot.event
@asyncio.coroutine
def on_ready():
    print('Logged in as:\n{0}({1})\n------'.format(bot.user.name, bot.user.id))

@bot.command(pass_context=True)  
@asyncio.coroutine
def quote(ctx, msg_id : str, *reply : str):
    try:
        msg_ = yield from bot.get_message(ctx.message.channel, msg_id)
        
        # Format output message
        if not reply:
            output = '**{0} [{1}] said:** _via {2}_ ```{3}```'.format(
                                msg_.author.name, 
                                msg_.timestamp.strftime("%Y-%m-%d %H:%M:%S"), 
                                ctx.message.author.name, 
                                msg_.clean_content
                        )
        else:
            output = '**{0} [{1}] said:** ```{2}``` **{3}:** {4}'.format(
                                msg_.author.name, 
                                msg_.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                msg_.clean_content, 
                                ctx.message.author.name, 
                                ' '.join(reply)
                        )
            
        yield from bot.say(output)
    except discord.errors.HTTPException:
        # Return error if message not found.
        yield from bot.say(("Quote not found in this channel ('{0}' "
                            + "requested by "
                            + "{1})").format(msg_id,
                                             ctx.message.author.name))

    # Clean up request regardless of success
    yield from bot.delete_message(ctx.message)

@bot.command(pass_context=True)  
@asyncio.coroutine
def misquote(ctx , target : discord.User):
    try:
#        if ctx.message.author.permissions_in(ctx.message.channel).administrator:

        user = target
        #if target[1] == "@":
        #    user = target
        #else:
        #    user = ctx.message.server.get_member(target)

        yield from bot.send_message(ctx.message.author,
                                    ('What would you like to be '
                                     + ' misattributed to ' 
                                     + user.name + '?'))

        def priv(msg):
            return msg.channel.is_private == True

        reply = yield from bot.wait_for_message(timeout=60.0, 
                                                author=ctx.message.author, 
                                                check=priv)

        faketime = datetime.datetime.now() - datetime.timedelta(minutes=5)

        yield from bot.say('**{0} [{1}] definitely said:** ```{2}```'.format(
                            user.name,
                            faketime.strftime("%Y-%m-%d %H:%M:%S"),
                            reply.clean_content
                            ))
#        else:
#            yield from bot.say("Insufficient Access")
        
    except discord.ext.commands.errors.BadArgument:
        yield from bot.say("User not found")

@bot.command()
@asyncio.coroutine
def frames(char : str, move : str, situ : str):
    try:
        c = char.lower()
        m = move.lower()
        s = situ.lower()

        # Handle Regional names
        if c == "bison":
            c = "dictator"
        if c == "vega":
            c = "claw"
        if c == "balrog":
            c = "boxer"

        # Handle crouch
        m = re.sub('cr\.', 'c.', m)

        with open('moves.json', 'r') as f:
            moves = ujson.loads(f.read())

        move = [i for i in moves[c] if i['name'] == m]

        if s == 'block':
            frames = move[0]['data']['blockAdvantage']

        if s == 'hit':
            frames = move[0]['data']['hitAdvantage']

        if frames > 1000:
            yield from bot.say(c + "'s " + m +
                               ' is **knockdown/launch** on ' + s)
        elif frames > 0:
            yield from bot.say(c + "'s " + m + " is **+" + str(frames) +
                               "** on " + s)
        elif frames == 0:
            yield from bot.say(c + "'s " + m + ' is **even** on ' + s)
        else:
            yield from bot.say(c + "'s " + m + ' is **' + str(frames) + 
                               '** on ' + s)

    except KeyError:
        yield from bot.say("Character Not Found")

    except IndexError:
        yield from bot.say("Move Not Found")

    except UnboundLocalError:
        yield from bot.say("Situation Not Found")

if __name__=='__main__':
    with open('token.txt', 'r') as token_file:
        token = token_file.read()

    bot.run(token)

