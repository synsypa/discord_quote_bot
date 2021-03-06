import datetime
import discord
from discord.ext import commands
import asyncio
import json
import ujson
import re
import logging
import sys
import os

# Configure logging
log = logging.getLogger(__name__)
fmt = logging.Formatter(u'\u241e'.join(['%(asctime)s',
                                        '%(name)s',
                                        '%(levelname)s',
                                        '%(funcName)s',
                                        '%(message)s']))
streamInstance = logging.StreamHandler(stream=sys.stdout)
streamInstance.setFormatter(fmt)
log.addHandler(streamInstance)
log.setLevel(logging.DEBUG)

# Load Frame Data json
with open('moves.json', 'r') as f:
    moves = ujson.loads(f.read())

def log_msg(data):
    """
    Accepts a list of data elements, removes the  u'\u241e'character
    from each element, and then joins the elements using u'\u241e'.
    
    Messages should be constructed in the format:
        
        {message_type}\u241e{data}

    where {data} should be a \u241e delimited row.
    """
    tmp = [d.replace(u'\u241e', ' ') for d in data]
    return u'\u241e'.join(tmp)

# Code
description = '''
            A Bot to provide Basic Quoting functionality for Discord
            '''

bot = commands.Bot(command_prefix='!', description=description)

@bot.event
@asyncio.coroutine
def on_ready():
    log.info(log_msg(['login', bot.user.name, bot.user.id]))

@bot.command(pass_context=True)  
@asyncio.coroutine
def me(ctx, *text : str):
    log.info(log_msg(['received_request', 
                      'me',
                      ctx.message.author.name, 
                      ctx.message.channel.name,
                      ' '.join(text)]))

    output = '_{0} {1}_'.format(
                                ctx.message.author.name, 
                                ' '.join(text)
                            )

    log.info(log_msg(['formatted_self', ' '.join(text)]))

    yield from bot.say(output)

    log.info(log_msg(['sent_message', 'me', ctx.message.channel.name]))

    # Clean up request regardless of success
    yield from bot.delete_message(ctx.message)
    log.info(log_msg(['deleted_request', ctx.message.id]))


@bot.command(pass_context=True)  
@asyncio.coroutine
def quote(ctx, msg_id : str, *reply : str):
    log.info(log_msg(['received_request', 
                      'quote',
                      ctx.message.author.name, 
                      ctx.message.channel.name,
                      msg_id]))
    try:
        msg_ = yield from bot.get_message(ctx.message.channel, msg_id)
        log.info(log_msg(['retrieved_quote', 
                          msg_id, 
                          ctx.message.channel.name,
                          msg_.author.name, 
                          msg_.timestamp.strftime("%Y-%m-%d %H:%M:%S"), 
                          ctx.message.author.name, 
                          msg_.clean_content]))

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
        log.info(log_msg(['formatted_quote', ' '.join(reply)]))
            
        yield from bot.say(output)

        log.info(log_msg(['sent_message', 'quote', ctx.message.channel.name]))

    except discord.errors.HTTPException:
        log.warning(['msg_not_found', msg_id, ctx.message.author.name])

        # Return error if message not found.
        yield from bot.say(("Quote not found in this channel ('{0}' "
                            + "requested by "
                            + "{1})").format(msg_id,
                                             ctx.message.author.name))
        log.info(log_msg(['sent_message', 
                          'invalid_quote_request', 
                          ctx.message.channel.name]))
 
    # Clean up request regardless of success
    yield from bot.delete_message(ctx.message)
    log.info(log_msg(['deleted_request', msg_id]))

@bot.command(pass_context=True)  
@asyncio.coroutine
def misquote(ctx , target : discord.User):

    log.info(log_msg(['received_request',
                      'misquote',
                      ctx.message.author.name,
                      ctx.message.channel.name,
                      target.name]))

    try:
#        if ctx.message.author.permissions_in(ctx.message.channel.name).administrator:

        user = target
        #if target[1] == "@":
        #    user = target
        #else:
        #    user = ctx.message.server.get_member(target)
       
        yield from bot.send_message(ctx.message.author,
                                    ('What would you like to be '
                                     + ' misattributed to ' 
                                     + user.name + '?'))

        log.info(log_msg(['sent_message', 'misquote_dm_request', user.name]))

        def priv(msg):
            return msg.channel.is_private == True

        reply = yield from bot.wait_for_message(timeout=60.0, 
                                                author=ctx.message.author, 
                                                check=priv)

        log.info(log_msg(['received_request', 
                          'misquote_response', 
                          ctx.message.author.name,
                          ctx.message.channel.name,
                          reply.clean_content]))

        faketime = datetime.datetime.now() - datetime.timedelta(minutes=5)

        yield from bot.say('**{0} [{1}] definitely said:** ```{2}```'.format(
                            user.name,
                            faketime.strftime("%Y-%m-%d %H:%M:%S"),
                            reply.clean_content
                            ))

        log.info(log_msg(['sent_message',
                          'misquote',
                           user.name,
                           faketime.strftime('%Y-%m-%d %H:%M:%S'),
                           reply.clean_content ]))
#        else:
#            yield from bot.say("Insufficient Access")
        
    except discord.ext.commands.errors.BadArgument:
        log.warning(log_msg(['user_not_found',
                             target,
                             ctx.message.author.name]))

        yield from bot.say("User not found")

        log.info(log_msg(['sent_message',
                          'invalid_misquote_request',
                          ctx.message.channel.name]))

@bot.command()
@asyncio.coroutine
def frames(char : str, move : str, situ : str=""):
    log.info(log_msg(['received_request',
                      'frames',
                      char,
                      move,
                      situ]))
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

        move = [i for i in moves[c] if i['name'] == m]
        
        # Responses for startup, active, recovery
        if s == 'startup' or s == 'recovery':

            if s == 'startup':
                frames = move[0]['data']['startupFrames']
                
            if s == 'recovery':
                frames = move[0]['data']['recoveryFrames']

            yield from bot.say("{0}'s  {1} has **{2}** frames of  {3}.".format(
                                c.capitalize(),
                                m,
                                str(frames),
                                s
                                ))
        
        # Responses for block and hit    
        elif s == 'block' or s == 'hit':

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

        # Responses for damage and stun
        elif s == 'damage' or s == 'stun':
            
            if s == 'damage':
                deeps = move[0]['data']['damageValue']
                
            else:
                deeps = move[0]['data']['stunValue']
                
            yield from bot.say("{0}'s {1} does **{2}** {3}.".format(
                                                                    c.capitalize(),
                                                                    m,
                                                                    deeps,
                                                                    s
                                                                   ))
        
        # For nothing, or anything else, respond with summary of frame data
        else:
            
            # Dictionary of key names and nice names for printed results
            dataNames = {'startupFrames': ('Startup', 0),
                         'activeFrames': ('Active', 1),
                         'recoveryFrames': ('Recovery', 2),
                         'blockAdvantage': ('On Block', 3),
                         'hitAdvantage': ('On Hit', 4),
                         'damageValue': ('Damage', 5),
                         'stunValue': ('Stun', 6)
                        }
            
            output = "{0}'s {1} frame data:\n".format(c.capitalize(), m)  
            
            # Add to output based on existing frame data
            for x in sorted(dataNames, key=lambda x : dataNames[x][1]):
            
                if x in move[0]['data']:
                    frames = move[0]['data'][x]
                    
                    # Deal with knockdowns
                    if x == 'hitAdvantage' and frames > 1000:
                        frames = "launch/knockdown"
                            
                    output += "{0}: **{1}**, ".format(dataNames[x][0], str(frames))
            
            # Remove last character (extra comma)        
            output = output[:-2]
            
            yield from bot.say(output)
        
    except KeyError:
        log.warning(log_msg(['frame_data_not_found', 'character',  c]))

        yield from bot.say("Character Not Found")

        log.info(log_msg(['sent_message',
                          'invalid_character_request',
                          ctx.message.channel.name]))

    except IndexError:
        log.warning(log_msg(['frame_data_not_found', 'move',  m]))

        yield from bot.say("Move Not Found")

        log.info(log_msg(['sent_message',
                          'invalid_move_request',
                          ctx.message.channel.name]))

    except UnboundLocalError:
        log.warning(log_msg(['frame_data_not_found', 'situation',  s]))
        
        yield from bot.say("Situation Not Found")

        log.info(log_msg(['sent_message',
                         'invalid_situation_request',
                          ctx.message.channel.name]))

if __name__=='__main__':
    if os.environ['DISCORD_QUOTEBOT_TOKEN']:
        log.info(log_msg(['token_read']))

    log.info(log_msg(['bot_intialize']))
    bot.run(os.environ['DISCORD_QUOTEBOT_TOKEN'])
    
