#telegram bot frontend
#by cozybear

# add libs
import sys
import os
import traceback
import logging
import requests
import time
import io
import asyncio
import base64
import json
import socket
import numpy as np
from PIL import Image
from pathlib import Path
import hashlib

#from multiprocessing import Pool, Queue, Process
import random
# crpyto bot payment
from aiocryptopay import AioCryptoPay, Networks
from datetime import datetime
import re

# gen id
from uuid import uuid4

# queuing server and handler
from redis import Redis

from rq import Queue, Worker
from rq.job import Job

from arq import create_pool
from arq.connections import RedisSettings
# add functions, database, config
from keyboards import *
from queue_handler import queue_request, turnover_request
from watermark import apply_watermark
from dbhelper import DBHelper
import config

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

#status bar lib
from tqdm.contrib.telegram import tqdm

#telegram python api lib
from telegram import ForceReply, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, LabeledPrice, constants
from telegram import __version__ as TG_VER

from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, \
    ContextTypes, MessageHandler, filters, CallbackContext, ConversationHandler, PreCheckoutQueryHandler,
    ShippingQueryHandler)


######################################################################################################

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

######################################################################################################
#logging

# Enable logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d - %H:%M:%S")
fh = logging.FileHandler("telegrambot.log", "a")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)

logging.basicConfig(filename='telegrambot.log', format='%(asctime)s - %(message)s',  level=logging.INFO)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
# set higher logging level for httpx to avoid all GET and POST requests being logged
#logging.getLogger("httpx").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)

def log_command(command):
    log.info(command)


def logs():
    message = ""
    with open("telegrambot.log", "r") as f:
        listoflogs = f.readlines()[-5:]
        for line in listoflogs:
            message += str(line)
    return message

######################################################################################################


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


######################################################################################################
######################################################################################################



async def start(update: Update, context: CallbackContext):
    try:
        chat_id = update.effective_chat.id
        first_name = update.effective_user.first_name
        username = update.effective_user.username

        # check if user is in database. if not, add him
        isOld = dbhelper.check_user(
            chat_id, username, first_name)

        # if user already in database, we can address him differently
        # if user is new
        if isOld == False:
            # update first active column with timestamp
            dbhelper.update_first_active(chat_id, datetime.now().isoformat(' ', 'seconds'))
            # update last active column
            dbhelper.update_last_active(chat_id, datetime.now().isoformat(' ', 'seconds'))

            # get (default) token amount when new
            available_tokens = dbhelper.get_user_tokens(chat_id)
            await context.bot.send_message(text=f"Welcome, *{first_name}* 👋\n\n\n"
                                                f"🔑 *1* token \= *1* generation\n\n"
                                                f"🏧 You have *{available_tokens}* FREE token"
                                                f"{'' if available_tokens==1 else 's'} left",
                                           chat_id=chat_id,
                                           reply_markup=reply_markup_start,
                                           parse_mode="MarkdownV2")

        # else if user is known already
        else:
            # update last active column
            dbhelper.update_last_active(chat_id, datetime.now().isoformat(' ', 'seconds'))

            # check if terms were accepted
            terms_accepted = dbhelper.check_terms(chat_id)
            available_tokens = dbhelper.get_user_tokens(chat_id)

            if terms_accepted == False:
                await context.bot.send_message(text=f"Welcome, *{first_name}* 👋\n\n\n"
                                                    f"🔑 *1* token \= *1* generation\n\n"
                                                    f"🏧 You have *{available_tokens}* token"
                                                    f"{'s' if available_tokens != 1 else ''} left",
                                               chat_id=chat_id,
                                               reply_markup=reply_markup_start,
                                               parse_mode="MarkdownV2")

            else:

                await context.bot.send_message(text=f"Welcome back, *{first_name}* 👋\n\n\n"
                                                    f"🔑 *1* token \= *1* generation\n\n"
                                                    f"🏧 You have *{available_tokens}* token"
                                                    f"{'s' if available_tokens!=1 else ''} left",
                                               chat_id=chat_id,
                                               reply_markup=reply_markup_button,
                                               parse_mode="MarkdownV2")



    except Exception as e:
        traceback.print_exc()


        

async def cancel(update: Update, context: CallbackContext):
    try:
        first_name = update.effective_user.first_name
        logger.info("User %s canceled the conversation.", first_name)
        await update.callback_query.message.reply_text(text="Bye! I hope we can talk again some day.",
                                                reply_markup=ReplyKeyboardRemove(),
                                       )



        return ConversationHandler.END

    except Exception as e:
        print(e)



async def agree_terms(update: Update, context: CallbackContext):
    try:
        with open('/user_agreement.txt', 'r') as file: # add path here
            user_agreement = file.read()
            await update.callback_query.message.edit_text(text=f"*In order to proceed, please read and accept the user agreement below:*\n\n"
                                                               f"{str(user_agreement)}",
                                                          reply_markup=reply_markup_agreement,
                                                          parse_mode="MarkdownV2"
                                                          )
    except Exception as e:
        print(e)


async def accepted_terms(update: Update, context: CallbackContext):
    try:
        dbhelper.accept_terms(update.effective_chat.id)
        available_tokens = dbhelper.get_user_tokens(update.effective_chat.id)

        first_name = update.effective_user.first_name
        await context.bot.send_message(text=f"Welcome back, *{first_name}* 👋\n\n\n"
                                            f"🔑 *1* token \= *1* generation\n\n"
                                            f"🏧 You have *{available_tokens}* token"
                                            f"{'s' if available_tokens != 1 else ''} left",
                                       chat_id=update.effective_chat.id,
                                       reply_markup=reply_markup_button,
                                       parse_mode="MarkdownV2")
    except Exception as e:
        print(e)



async def declined_terms(update: Update, context: CallbackContext):
    try:
        first_name = update.effective_user.first_name
        available_tokens = dbhelper.get_user_tokens(update.effective_chat.id)

        await context.bot.send_message(text=f"Welcome back, *{first_name}* 👋\n\n\n"
                                            f"🔑 *1* token \= *1* generation\n\n"
                                            f"🏧 You have *{available_tokens}* token"
                                            f"{'s' if available_tokens != 1 else ''} left",
                                       chat_id=update.effective_chat.id,
                                       reply_markup=reply_markup_start,
                                       parse_mode="MarkdownV2")
    except Exception as e:
        print(e)


# /terms command
async def terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open('legal/user_agreement.txt', 'r') as file:
            user_agreement = file.read()
            await update.message.reply_text(text=user_agreement,
                                            reply_markup=reply_markup_start
        )

    except Exception as e:
        print(e)



async def back_to_menu(update: Update, context: CallbackContext):
    try:
        chat_id = update.effective_chat.id
        first_name = update.effective_user.first_name
        username = update.effective_user.username

        # update last active column
        dbhelper.update_last_active(chat_id, datetime.now().isoformat(' ', 'seconds'))

        # check if terms were accepted
        terms_accepted = dbhelper.check_terms(chat_id)
        available_tokens = dbhelper.get_user_tokens(chat_id)

        if terms_accepted == False:
            await update.callback_query.message.edit_text(text=f"Welcome back, *{first_name}* 👋\n\n\n"
                                                               f"🔑 *1* token \= *1* generation\n\n"
                                                               f"🏧 You have *{available_tokens}* token"
                                                               f"{'' if available_tokens == 1 else 's'} left",
                                                          reply_markup=reply_markup_start,
                                                          parse_mode='MarkdownV2')


        else:
            await update.callback_query.message.edit_text(text=f"Welcome back, *{first_name}* 👋\n\n\n"
                                                               f"🔑 *1* token \= *1* generation\n\n"
                                                               f"🏧 You have *{available_tokens}* token"
                                                               f"{'' if available_tokens==1 else 's'} left",
                                                          reply_markup=reply_markup_button,
                                                          parse_mode='MarkdownV2')
    except Exception as e:
        print(e)



async def button(update: Update, context: CallbackContext):
    try:
        # update last active column
        dbhelper.update_last_active(update.effective_chat.id, datetime.now().isoformat(' ', 'seconds'))

        query = update.callback_query
        await query.answer()

        if query.data == '1':
            await context.bot.send_message(text="*Please enter your prompts\!*",
                                            chat_id=update.effective_chat.id,
                                            reply_markup=reply_markup_menu,
                                            parse_mode='MarkdownV2')
            return GENERATE

        elif query.data == '2':
            user_id = update.effective_chat.id
            hashed_user_id = hashlib.md5(np.int32(user_id)).hexdigest()
            
            await update.callback_query.message.edit_text(text=f"Your User *ID* is:\n\n{hashed_user_id}",
                                                          reply_markup=reply_markup_menu,
                                                          parse_mode='MarkdownV2')

        elif query.data == '4':
            await update.callback_query.message.edit_text(text="👇 Please check the available options below\n\n"
                                                               "*1* token \= *$0\.5* *USD*\n"
                                                               "*2* tokens \= *$0\.95* *USD*\n"# \(*0\.475*/token\)
                                                               "*5* tokens \= *$2\.2* *USD*\n"# \(*0\.44*/token\) 
                                                               "*10* tokens \= *$4* *USD*\n\n"# \(*0\.4*/token\)
                                                               "Your contribution helps us cover the costs of operation\.\n\n"
                                                               "🙏 *Thank you\!*",
                                                          reply_markup=reply_markup_buyoptions,
                                                          parse_mode='MarkdownV2')

        return ConversationHandler.END

    except Exception as e:
        print(e)



######################################################################################################
######################################################################################################

async def get_prompts(update: Update, context: CallbackContext):
    try:
        await update.message.reply_text(text=f"Thank you, please wait...\n\n\n\n\n"
                                        )

        #check queue status
        user_queue_status = dbhelper.check_queue_status(update.effective_chat.id)
        # get sql token customer balance
        token_balance = dbhelper.get_user_tokens(update.effective_chat.id)
        #check queue length
        queue_length = int(q.count)
        # set limit
        queue_limit = 20

        # check if user is not in queue and has enough tokens and there are max 19 people in queue
        if user_queue_status and token_balance > 0 and queue_length < queue_limit:
            # set queue status to True
            dbhelper.user_in_queue(update.effective_chat.id)

            msg = await update.message.reply_text(text=f"✅ Accepted\n\n\n\n\n"
                                                       f"󠀠󠀠🎴🎴🎴🎴🎴🎴🎴🎴🎴🎴🎴🎴󠀠",
                                                  )

            context.user_data["msg"] = msg

            # get photo
            await context.bot.edit_message_text(text=f"✅ Accepted\n\n\n⏳ *Loading resources*\.\.\.\n\n"
                                                     f"🃏🎴🎴🎴🎴🎴🎴🎴🎴🎴🎴🎴",
                                                parse_mode='MarkdownV2',
                                                chat_id=update.message.chat_id,
                                                message_id=msg.message_id,
                                                )
            await asyncio.sleep(0.2)

            await context.bot.edit_message_text(text=f"✅ Accepted\n\n\n⏳ *Forwarding prompts*\.\.\.\n\n"
                                                     f"🃏🃏🎴🎴🎴🎴🎴🎴🎴🎴🎴🎴",
                                                parse_mode='MarkdownV2',
                                                chat_id=update.message.chat_id,
                                                message_id=msg.message_id,
                                                )

            # get user prompt input
            user_prompts = await update.message.text

            await context.bot.edit_message_text(text=f"✅ Accepted\n\n\n⏳ *Queuing request*\.\.\.\n\n"
                                                     f"🃏🃏🃏🎴🎴🎴🎴🎴🎴🎴🎴🎴",
                                                parse_mode='MarkdownV2',
                                                chat_id=update.message.chat_id,
                                                message_id=msg.message_id,
                                                )
            await asyncio.sleep(0.2)

            await context.bot.edit_message_text(text=f"✅ Accepted\n\n\n⏳ *Queuing request*\.\.\.\n\n"
                                                     f"🃏🃏🃏🃏🎴🎴🎴🎴🎴🎴🎴🎴",
                                                parse_mode='MarkdownV2',
                                                chat_id=update.message.chat_id,
                                                message_id=msg.message_id,
                                                )


            # call sd function
            print(f"{datetime.now().isoformat(' ', 'seconds')} Starting generation...\n")

            user_id = update.effective_chat.id
            hashed_user_id = hashlib.md5(np.int32(user_id)).hexdigest()
            path_of_img = await generate(update, context, hashed_user_id, user_prompts)


            """
            # apply watermark
            await context.bot.edit_message_text(text=f"✅ Accepted\n\n\n⏳ *Applying watermark*\.\.\.\n\n"
                                                     f"🃏🃏🃏🃏🃏🃏🃏🃏🃏🃏🃏🎴",
                                                parse_mode='MarkdownV2',
                                                chat_id=update.message.chat_id,
                                                message_id=msg.message_id,
                                                )
            await asyncio.sleep(0.5)

            logo_path = "/logo.png"
            apply_watermark("bottomright", logo_path, path_of_img)
            """

            await context.bot.edit_message_text(text=f"✅ Accepted\n\n\n*Done*\.\n\n"
                                                     f"🃏🃏🃏🃏🃏🃏🃏🃏🃏🃏🃏🃏",
                                                parse_mode='MarkdownV2',
                                                chat_id=update.message.chat_id,
                                                message_id=msg.message_id,
                                                )

            # send generated photo back to user
            print(f"{datetime.now().isoformat(' ', 'seconds')} Sending image back to user...\n")
            chat_id = update.message.chat_id
            await context.bot.send_photo(caption="🦾 Powered by Bot",
                                         photo=open(path_of_img, 'rb'),
                                         #reply_to_message_id=msg.message_id,
                                         chat_id=chat_id
                                         )


            # write off 1 token from customer balance
            dbhelper.writeoff_token(chat_id)
            # free queue for user
            dbhelper.user_notin_queue(chat_id)
            # update last active column
            dbhelper.update_last_active(chat_id, datetime.now().isoformat(' ', 'seconds'))
            # update jobs_completed
            dbhelper.update_jobs_completed(chat_id)
            # get new (updated) user token amount
            available_tokens = dbhelper.get_user_tokens(chat_id)

            await context.bot.send_message(text="😎 Waiting on your next request\.\.\.\n\n\n"
                                                f"🔑 *1* token \= *1* generation\n\n"
                                                f"🏧 You have *{available_tokens}* token"
                                                f"{'s' if available_tokens != 1 else ''} left",
                                           chat_id=update.effective_chat.id,
                                           reply_markup=reply_markup_button,
                                           parse_mode='MarkdownV2')

            return ConversationHandler.END

        # if not in queue but not enough tokens...
        elif token_balance == 0:
            await context.bot.send_message(text=f"❌ Declined\n\n\n"
                                                 f"Uh\-oh, it seems like you have no more tokens left\."
                                                 f"\n\nPlease first buy tokens before proceeding\!",
                                            chat_id=update.effective_chat.id,
                                            reply_markup=reply_markup_tokens_menu,
                                            parse_mode='MarkdownV2')
        # if user already in queue...
        elif not user_queue_status:
            await context.bot.send_message(text=f"❌ Declined\n\n\n"
                                                 f"We are currently processing your previous request, "
                                                 f"please wait until it is finished before making a new request\.\n\n"
                                                 f"*Thank you for your patience\!* 🥰",
                                            chat_id=update.effective_chat.id,
                                            reply_markup=reply_markup_menu,
                                            parse_mode='MarkdownV2')

        # if too many requests
        elif queue_length >= queue_limit:
            await context.bot.send_message(text=f"❌ Declined\n\n\n"
                                                f"The Bot is currently busy as we are receiving too many requests\."
                                                f"Please try again later\!\n\n"
                                                f"*Thank you for your patience\!* 🥰",
                                           chat_id=update.effective_chat.id,
                                           reply_markup=reply_markup_menu,
                                           parse_mode='MarkdownV2')

        # fallback
        else:
            await context.bot.send_message(text="⚠️ Something went wrong\.\.\.",
                                           chat_id=update.effective_chat.id,
                                           reply_markup=reply_markup_menu,
                                           parse_mode='MarkdownV2')



    except Exception as e:
        traceback.print_exc()




async def generate(update: Update, context: CallbackContext, hashed_user_id, prompts):
    try:
        msg = context.user_data.get("msg", 'Not found')

        await context.bot.edit_message_text(text=f"✅ Accepted\n\n\n⏳ *Connecting to backend*\.\.\.\n\n"
                                                 f"🃏🃏🃏🃏🃏🎴🎴🎴🎴🎴🎴🎴",
                                            parse_mode='MarkdownV2',
                                            chat_id=update.message.chat_id,
                                            message_id=msg.message_id,
                                            )

        # check if webui backend running on localhost port
        port = 7860 # change default port if needed
        while True:
            if is_port_in_use(port) == False:  # if port not in use, try again after 5 seconds
                await asyncio.sleep(5)
                continue

            else:  # if port in use (backend active), break loop and proceed
                break


        await context.bot.edit_message_text(text=f"✅ Accepted\n\n\n⏳ *Preparing payload*\.\.\.\n\n"
                                                 f"🃏🃏🃏🃏🃏🃏🃏🃏🎴🎴🎴🎴",
                                            parse_mode='MarkdownV2',
                                            chat_id=update.message.chat_id,
                                            message_id=msg.message_id,
                                            )

        await asyncio.sleep(0.3)

        await context.bot.edit_message_text(text=f"✅ Accepted\n\n\n⏳ *Start generating*\.\.\.\n\n"
                                                 f"🃏🃏🃏🃏🃏🃏🃏🃏🃏🃏🎴🎴",
                                            parse_mode='MarkdownV2',
                                            chat_id=update.message.chat_id,
                                            message_id=msg.message_id,
                                            )
        await asyncio.sleep(0.2)

        
        job = q.enqueue(queue_request, args=(hashed_user_id, prompts), job_timeout=10000,
                        result_ttl=30)  # timeout if job takes more than 30 minutes, keep results for 30 seconds

        queue_length = int(q.count)


        await context.bot.edit_message_text(text=f"✅ Accepted\n\n\n"
                                                 f"{f'You are first in queue{chr(92)}!' if queue_length == 0 else f'You are position *{queue_length + 1}* in queue{chr(92)}!'}"
                                                 f"\n\n⏳ *Generating*\.\.\.\n\n"
                                                 f"🃏🃏🃏🃏🃏🃏🃏🃏🃏🃏🎴🎴",
                                            parse_mode='MarkdownV2',
                                            chat_id=update.message.chat_id,
                                            message_id=msg.message_id,
                                            )


        while True:
            # when job is queued and response is none, sleep and try again
            if job.return_value() is None:
                await asyncio.sleep(5)
                continue
            # else, break loop and proceed
            else:
                break

        response = job.return_value()

        # decode reponse and return path of image
        for idx, i in enumerate(response['images']):
            await context.bot.edit_message_text(text=f"✅ Accepted\n\n\n⏳ *Decoding response*\.\.\.\n\n"
                                                     f"🃏🃏🃏🃏🃏🃏🃏🃏🃏🃏🃏🎴",
                                                parse_mode='MarkdownV2',
                                                chat_id=update.message.chat_id,
                                                message_id=msg.message_id,
                                                )

            image = Image.open(io.BytesIO(base64.b64decode(i.split(",", 1)[0])))
            path_of_final_img = f'output/output_{idx}_{hashed_user_id}.png'
            image.save(path_of_final_img)

            path = Path(path_of_final_img).absolute()

            return path


    except Exception as e:
        traceback.print_exc()

######################################################################################################
######################################################################################################
# payment functions

# start payment process
async def start_with_payment_callback(update: Update, context: CallbackContext):
    try:
        username = update.effective_user.first_name
        terms_accepted = dbhelper.check_terms(update.effective_chat.id)
        available_tokens = dbhelper.get_user_tokens(update.effective_chat.id)

        if terms_accepted == False:
            await context.bot.send_message(text=f"Welcome, *{username}* 👋\n\n\n"
                                                f"🔑 *1* token \= *1* generation\n\n"
                                                f"🏧 You have *{available_tokens}* token"
                                                f"{'s' if available_tokens != 1 else ''} left",
                                           chat_id=update.effective_chat.id,
                                           reply_markup=reply_markup_start,
                                           parse_mode="MarkdownV2")

        else:
            # catch callback data
            callback_key = int(update.callback_query.data)
            context.user_data["tokens_to_buy"] = token_translation.get(callback_key)

            await update.callback_query.message.edit_text(text=f"Please select your payment method\:",
                                                          reply_markup=reply_markup_payment_methods,
                                                          parse_mode='MarkdownV2')

    except Exception as e:
        print(e)



# crypto payment
async def select_crypto_asset(update: Update, context: CallbackContext):
    try:
        await update.callback_query.message.edit_text(text=f"Please select your cryptocurrency\:",
                                                      reply_markup=reply_markup_cryptoassets,
                                                      parse_mode='MarkdownV2')

    except Exception as e:
        print(e)


async def crypto_payment_callback(update: Update, context: CallbackContext):
    try:
        # choose payment net
        #crypto = AioCryptoPay(token=config.crypto_token_real, network=Networks.MAIN_NET)
        crypto = AioCryptoPay(token=config.crypto_token_test, network=Networks.TEST_NET)

        token_amount = context.user_data.get("tokens_to_buy", 'Not found')
        token_price = price_translation.get(token_amount)

        target_fiat = 'USD'
        target_asset = update.callback_query.data #'USDT'

        # Get amount in crypto by fiat sum
        amount = await crypto.get_amount_by_fiat(summ=token_price, asset=target_asset, target=target_fiat)

        # round and escape . and -
        amount_str = str(round(amount, 7)).replace('.', '\.').replace('-', '\-')
        token_price_str = str(token_price).replace('.', '\.')

        # set invoice expiry time
        expiry_time = 60
        description = f"{str(token_amount)} Generation Token{'' if token_amount == 1 else 's'} "
        hidden_message = "Thank you for your payment! 🥰"
        
        invoice = await crypto.create_invoice(asset=target_asset,
                                              amount=amount,
                                              description=description,
                                              hidden_message=hidden_message,
                                              expires_in=expiry_time
                                              )

        await context.bot.send_message(text=f"Please click the link below to pay with Crypto Bot\!\n\n"
                                            f"Buy *{str(token_amount)}* Generation Token{'' if token_amount == 1 else 's'} "
                                            f"for *{amount_str} {str(target_asset)}* "
                                            f"*\({token_price_str} {target_fiat}\)*?\n\n\n"
                                            f"[Pay with Crypto Bot]({invoice.pay_url})\n\n"
                                            f"This invoice will expire in *{str(expiry_time)}* seconds\.",
                                       chat_id=update.effective_chat.id,
                                       parse_mode='MarkdownV2',
                                       )

        # check invoice status
        while True:
            invoices = await crypto.get_invoices(invoice_ids=invoice.invoice_id)
            # when still active, continue loop
            if invoices.status == "active":
                await asyncio.sleep(2)
                # time.sleep(3)
                continue

            # when paid, update tokens and show menu
            elif invoices.status == "paid":
                dbhelper.update_tokens(update.effective_chat.id, int(token_amount))
                available_tokens = dbhelper.get_user_tokens(update.effective_chat.id)

                # do something after successfully receiving payment
                await context.bot.send_message(text="*🙌 Success\n\n🥰 Thank you for your payment\!*\n\n\n"
                                                    f"🏧 You now have *{str(available_tokens)}* token"
                                                    f"{'s' if available_tokens != 1 else ''} available\.\n\n"
                                                    f"😎 Waiting on your next request\.\.\.",
                                               reply_markup=reply_markup_button,
                                               chat_id=update.effective_chat.id,
                                               parse_mode='MarkdownV2')
                break
            # when expired, show menu and break loop
            elif invoices.status == "expired":
                await context.bot.send_message(text="😮 Invoice has expired\. Please try again\!",
                                               chat_id=update.effective_chat.id,
                                               reply_markup=reply_markup_buyoptions,
                                               parse_mode='MarkdownV2')
                break
            # fallback
            else:
                await context.bot.send_message(text="⚠️ Something went wrong\.\.\.",
                                               chat_id=update.effective_chat.id,
                                               reply_markup=reply_markup_button,
                                               parse_mode='MarkdownV2')
                break

    except Exception as e:
        print(e)



async def coming_soon(update: Update, context: CallbackContext):
    await context.bot.send_message(text="⚠️ Card payment coming soon\!\n\n"
                                        "Please select another payment method\:",
                                   chat_id=update.effective_chat.id,
                                   reply_markup=reply_markup_payment_methods,
                                   parse_mode='MarkdownV2')
    

# card payment
async def start_with_cash_payment_callback(update: Update, context: CallbackContext):
    try:
        #value = tokens_to_buy
        value = context.user_data.get("tokens_to_buy", 'Not found')
        title = f"{value} Token{'' if value==1 else 's'}"
        description = f"\nBuy {value} access token{'' if value==1 else 's'}!"
        # select a payload just for you to recognize its the donation from your bot
        payload = "bot_signature"
        # In order to get a provider_token see https://core.telegram.org/bots/payments#getting-a-token
        currency = "EUR"
        # price * 100 so as to include 2 decimal points
        prices = [LabeledPrice("Test", value * 100)]

        chat_id = update.effective_chat.id
        # optionally pass need_name=True, need_phone_number=True,
        # need_email=True, need_shipping_address=True, is_flexible=True
        await context.bot.send_invoice(chat_id,
                                       title,
                                       description,
                                       payload,
                                       config.PAYMENT_PROVIDER_TOKEN,
                                       currency,
                                       prices,
                                       )

    except Exception as e:
        print(e)



# the pre-checkout card payment
async def precheckout_callback(update: Update, context: CallbackContext):
    try:
        """Answers the PreQecheckoutQuery"""
        query = update.pre_checkout_query
        # check the payload, is this from your bot?
        if query.invoice_payload != "bot_signature":
            # answer False pre_checkout_query
            await query.answer(ok=False, error_message="⚠️ Something went wrong...")
        else:
            await query.answer(ok=True)

    except Exception as e:
        print(e)




# finally, after contacting the card payment provider...
async def successful_payment_callback(update: Update, context: CallbackContext):
    try:
        """Confirms the successful payment."""
        tokens_to_buy = context.user_data.get("tokens_to_buy", 'Not found')
        dbhelper.update_tokens(update.effective_chat.id, tokens_to_buy)
        
        available_tokens = dbhelper.get_user_tokens(update.effective_chat.id)

        # do something after successfully receiving payment
        await update.message.reply_text(text="Thank you for your payment 🥰\!\n\n\n"
                                             f"You now have *{available_tokens}* available token"
                                             f"{'' if available_tokens==1 else 's'}\.",
                                       reply_markup=reply_markup_button,
                                       parse_mode='MarkdownV2')
    except Exception as e:
        print(e)

######################################################################################################

async def post_stop(application: Application) -> None:
    try:
        list_of_user_ids = dbhelper.get_user_ids()
        #list_of_user_ids=[761275954, 6253045986]
        print(list_of_user_ids)
        for user_id in list_of_user_ids:
            await application.bot.send_message(chat_id=user_id, text="🛠️ Bot is currently down for maintenance...\n\n"
                                                                     "🔁 Please try again later!")

    except Exception as e:
        print(e)
######################################################################################################
######################################################################################################

# call SQL database helper class
dbhelper = DBHelper()
dbhelper.setup()
# set queue status to False for every user
dbhelper.cancel_queue_status()


# init Redis server queue
redis_conn = Redis()
q = Queue('webui-backend', connection=redis_conn)



# create conversation states
GENERATE = range(1)

# callback token amount translation dict
token_translation = {6:1, 7:2, 8:5, 9:10, 10:20, 11:50, 12:100, 13:200, 19:500, 20:1000}

# token amount price translation
price_translation = {1:0.5, 2:0.95, 5:2.2, 10:4}



# main
def main():
    try:
        """Start the bot."""
        # Create the Application and pass it your bot's token.
        application = Application.builder().token(config.token).concurrent_updates(True).build() # .post_stop(post_stop)

        # on different commands - answer in Telegram
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("cancel", cancel))
        application.add_handler(CommandHandler("terms", terms))

        # back to menu handler
        application.add_handler(CallbackQueryHandler(back_to_menu, pattern='3'))

        # accept terms handler
        application.add_handler(CallbackQueryHandler(agree_terms, pattern='16'))
        application.add_handler(CallbackQueryHandler(declined_terms, pattern='17'))
        application.add_handler(CallbackQueryHandler(accepted_terms, pattern='18'))


        # payment handler
        # Add command handler to start the payment invoice
        application.add_handler(CallbackQueryHandler(start_with_payment_callback, pattern='6'))
        application.add_handler(CallbackQueryHandler(start_with_payment_callback, pattern='7'))
        application.add_handler(CallbackQueryHandler(start_with_payment_callback, pattern='8'))
        application.add_handler(CallbackQueryHandler(start_with_payment_callback, pattern='9'))
        application.add_handler(CallbackQueryHandler(start_with_payment_callback, pattern='10'))
        application.add_handler(CallbackQueryHandler(start_with_payment_callback, pattern='11'))
        application.add_handler(CallbackQueryHandler(start_with_payment_callback, pattern='12'))
        application.add_handler(CallbackQueryHandler(start_with_payment_callback, pattern='13'))
        application.add_handler(CallbackQueryHandler(start_with_payment_callback, pattern='19'))
        application.add_handler(CallbackQueryHandler(start_with_payment_callback, pattern='20'))
        #

        application.add_handler(CallbackQueryHandler(select_crypto_asset, pattern='14'))
        application.add_handler(CallbackQueryHandler(crypto_payment_callback, pattern='USDT'))
        application.add_handler(CallbackQueryHandler(crypto_payment_callback, pattern='TON'))
        application.add_handler(CallbackQueryHandler(crypto_payment_callback, pattern='BTC'))
        application.add_handler(CallbackQueryHandler(crypto_payment_callback, pattern='ETH'))
        application.add_handler(CallbackQueryHandler(crypto_payment_callback, pattern='LTC'))
        application.add_handler(CallbackQueryHandler(crypto_payment_callback, pattern='BNB'))
        application.add_handler(CallbackQueryHandler(crypto_payment_callback, pattern='TRX'))
        application.add_handler(CallbackQueryHandler(crypto_payment_callback, pattern='USDC'))


        #application.add_handler(CallbackQueryHandler(start_with_cash_payment_callback, pattern='15'))
        application.add_handler(CallbackQueryHandler(coming_soon, pattern='15'))




        # Pre-checkout handler to final check
        application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
        # Success! Notify your user!
        application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

        # conversation handler
        img2img_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(button)],
            states={
                GENERATE: [MessageHandler(filters.TEXT, get_prompts)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            allow_reentry=True,
        )
        # add conversation handler to app
        application.add_handler(img2img_conv_handler)


        # Run the bot until the user presses Ctrl-C
        application.run_polling(allowed_updates=Update.ALL_TYPES)

        
    except KeyboardInterrupt:
        print('\nYou pressed Ctrl+C! Exiting...\n')

    except Exception as e:
        traceback.print_exc()

    finally:
        # set queue status to False for every user
        dbhelper.cancel_queue_status()
        # exit
        sys.exit(0)
# main
if __name__ == "__main__":
    main()

