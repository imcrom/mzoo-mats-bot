from telegram import Update
from telegram.constants import ParseMode
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, PicklePersistence, CallbackQueryHandler
import logging
import aiohttp
import aiofiles
import asyncio
import math
import os
import re
import json
import io
import telegram
from PIL import ImageDraw, ImageFont, Image

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_photo("https://i.ibb.co/McSPGVq/ordinal.jpg", caption=f'Greetings <b>{update.message.from_user.first_name}</b>!,\n\nI am <b>Ordinal Paw Bot</b>, I am a private bot that <b> Ordinal Paw </b> owns.\
                                    \n\nI can generate your desired images in pixelated high quality version. You can use the <b>/opaw</b> followed by the prompt you want to generate your image with\
                                        \n\neg.\n`<b>/opaw</b> <i>Moon, chart, green, bullish</i>`\n\n',
                                    parse_mode=ParseMode.HTML
                                    )

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    inputs = update.message.text.split()[1:]  # Split the message and get all inputs after the /gen command
    prompt = " ".join(inputs)
    print(prompt)

    if not inputs:
        await context.bot.send_message(
            chat_id=update.message.chat.id,
            text=f'Hello {update.message.from_user.first_name}, Please enter the inputs after the /opaw command',
        )
        return
    
        # Check if there is a URL in the prompt variable
    url_regex = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    match = re.search(url_regex, prompt)
    if match:
        # Print the URL found in the prompt
        url = match.group()
        print(f"URL found in prompt: {url}")
        prompt = re.sub(url_regex, '', prompt)

        # Do something with the URL, e.g. download the content
    else:
        # Do something else if there's no URL
        print("No URL found in prompt.")

    await getModel(update, context, prompt, update.message.from_user.username, url)
    
async def getModel(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt, username, url) -> None:

    print(prompt)
    
    model = 'realistic-vision-v13'

    await context.bot.send_message (
        chat_id=update.message.chat.id,
        text=f'Request of: <b>{username}</b>\n\nGeneral Prompts:\n(<b>{prompt}</b>)\n\n<b>Please wait while we process your request.</b>\n',
        parse_mode=ParseMode.HTML
    )
    await requestApi(update.message, prompt, model, context, username, url)
    
async def upscale(update: Update, downloadUrl, context: ContextTypes.DEFAULT_TYPE, username) -> None:
    url = 'https://stablediffusionapi.com/api/v3/super_resolution'
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "key": "YimEHAg0HxDBkYtZp7X8ZEv7u84XWtt66TgVA78BnGWQlLHe6cdoDQREjpV5",
        "url": downloadUrl,
        "scale": 3,
        "webhook": 'null',
        "face_enhance": 'false'
    }
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                print(data)
                if resp.status == 200:
                    if data['status'] == 'success':
                        try:
                            await context.bot.send_photo(
                                chat_id=update.chat.id,
                                photo=data['output'],
                                caption=f'Request of: <b>{username}</b>\n\nHere is your upscaled image.',
                                parse_mode=ParseMode.HTML
                                
                            )
                        except Exception as e:
                            await context.bot.send_message(
                                chat_id=update.chat.id,
                                text=f'Request of: <b>{username}</b>\n\n<b>Sorry, we were unable to upscale your image.</b>\n\n Please try again. {e}',
                                parse_mode=ParseMode.HTML
                            )
                        break
                    if data['status'] == 'processing' and data['messege'] == 'Request processing':
                        print('Requesting again')
                        await upscale(update, downloadUrl, context, username)
                    if data['status'] == 'processing' and data['messege'] == 'Try to fetch request after given estimated time':
                        if 'fetch_result' in data:
                            url = data['fetch_result']
                        if 'eta' in data:
                            eta = data['eta']
                            await processing_update(update, eta, context)
                            await asyncio.sleep(math.ceil(eta))
                        continue
                    if data['status'] == 'error':
                        await error_update(update, context, username)
                        break
                    if data['status'] == 'failed':
                        continue
                    else:
                        raise Exception(f'Request failed with status code {resp.status}')


async def requestApi(update: Update, prompt, model, context: ContextTypes.DEFAULT_TYPE, username: str, link) -> None:

    print('MODEL THAT WILL BE USED: ', model)
    url = 'https://stablediffusionapi.com/api/v3/dreambooth/img2img'
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "key": "YimEHAg0HxDBkYtZp7X8ZEv7u84XWtt66TgVA78BnGWQlLHe6cdoDQREjpV5",
        "model_id": 'realistic-vision-v13',
        "prompt": prompt,
        "negative_prompt": 'null',
        "init_image": link,
        "width": "632",
        "height": "640",
        "samples": "1",
        "num_inference_steps": "30",
        "guidance_scale": 7.5,
        "safety_checker":"yes",
        "strength": 0.7,
        "seed": 'null',
        "webhook": 'null',
        "track_id": 'null'
    }
    
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                print(data)
                if resp.status == 200:
                    if data['status'] == 'success':
                        await context.bot.send_message(
                            chat_id=update.chat.id,
                            text=data['output'],
                        )
                        return
                    if data['status'] == 'processing' and data['messege'] == 'Request processing':
                        print('Requesting again')
                        await requestApi(update, prompt, model, context, username, link)
                    if data['status'] == 'processing' and data['messege'] == 'Try to fetch request after given estimated time':
                        if 'fetch_result' in data:
                            url = data['fetch_result']
                        if 'eta' in data:
                            eta = data['eta']
                            await processing_update(update, eta, context)
                            await asyncio.sleep(math.ceil(eta))
                        continue
                    if data['status'] == 'error':
                        await error_update(update, context, username)
                        break
                    if data['status'] == 'failed':
                        continue
                    else:
                        raise Exception(f'Request failed with status code {resp.status}')
                    
async def downloadImage(id: int, downloadUrl: str, update: Update, prompt: str, model: str, context: ContextTypes.DEFAULT_TYPE, username: str) -> None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(downloadUrl) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(f'{id}.png', mode='wb')
                    await f.write(await resp.read())
                    # call watermark function
                    if await add_watermark(f'{id}.png', '', update, context, username) == False:
                        await send_image(update, id, prompt, model, downloadUrl, context, username)
                        os.remove(f'{id}.png')
                        os.remove(f'{id}_watermarked.png')
                        await f.close()
    except Exception as e:
        print(f'An error occurred: {e}')

async def processing_update(update: Update, eta: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    eta = math.ceil(eta)

    if update.from_user.first_name == 'AI Gone Wild Generator' or update.from_user.first_name == 'test aigw':
        text='Image recreation is still on going please wait, Thank you for waiting. \n\nETA: {0} seconds.\n'.format(math.ceil(eta))
    else:
        text='Hi {0}!\n\nYour image is still being processed, Thank you for waiting. \n\n<b>ETA: {1} seconds.</b>\n'.format(update.from_user.first_name, math.ceil(eta))
 
    await context.bot.send_message(
		chat_id=update.chat.id,
        text=text,
        parse_mode=ParseMode.HTML
	)
    
async def error_update(update: Update, context: ContextTypes.DEFAULT_TYPE, username) -> None:
    if update.from_user.first_name == 'AI Gone Wild Generator' or update.from_user.first_name == 'test aigw':
        text = 'Image recreation failed, please try again later.\n'
    else:
        text= 'Hi {update.from_user.first_name}!\n\nDue to in-demand accesses and requests your image cannot be generated.\n\nPlease try again later.\n'
    await context.bot.send_message(
            chat_id=update.chat.id,
            text = f'{text}'
        )
        
async def send_image(update: Update, file_name: str, prompt: str, model: str, download_url: str, context: ContextTypes.DEFAULT_TYPE, username) -> None:
    with open(f'{file_name}_watermarked.png', 'rb') as file:

        
        await context.bot.send_photo(
            chat_id=update.chat.id,
            caption= f'Request of: <b>{username}\n\n</b><b>Image created with {model}</b>!\n\nGeneral Prompt:\n(<b>{prompt}</b>)\n\nModel: <b>{model}</b>\n\n<b>🐾 Ordinal Paw Bot 🐾</b>',
            photo=telegram.InputFile(file),
            parse_mode=ParseMode.HTML,
        )
        
async def add_watermark(file_path: str, watermark_text: str, update: Update, context: ContextTypes.DEFAULT_TYPE, username) -> None:
    async with aiofiles.open(file_path, "rb") as file:
        img_data = await file.read()
        try:
            with io.BytesIO(img_data) as img_stream:
                img = Image.open(img_stream)
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype('FeatureMono-Bold.ttf', 24)
                
                textwidth = draw.textlength(watermark_text, font)
                textheight = font.getsize(watermark_text)[1]

                width, height = img.size
                x = width / 2 - textwidth / 2
                y = height - textheight - 300

                draw.text((x, 400), watermark_text, font=font)
            
                new_file_path = file_path.split('.')[0] + '_watermarked.png'
                img.save(new_file_path)
                return False
        except OSError as e:
            await context.bot.send_message (
                chat_id=update.chat.id,
                text=f'<b>Sorry {username}, We have detected NSFW content in your image, please try again with a different prompt.</b>',
                parse_mode=ParseMode.HTML
                )
            return True

                
                
                    
persistence = PicklePersistence(filepath="arbitrarycallbackdatabot")
app = ApplicationBuilder().token("5851341881:AAFi9Pt2XTdtNlcH-dPyXtWzeHKfEu_u90A").persistence(persistence).arbitrary_callback_data(True).build()

app.add_handler(CommandHandler("start", hello))
app.add_handler(CommandHandler("opaw", gen))
app.add_handler(CallbackQueryHandler(getModel))
app.run_polling()