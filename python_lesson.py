import discord
from discord.ext import commands
import datetime
import asyncio
import pytz
import os.path
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Discordボットのトークン
DISCORD_TOKEN = "DISCORD_TOKEN"

# GoogleカレンダーAPIの設定
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Discordボットの設定
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 新しいイベントを作成する関数
async def create_event(ctx, summary, start_time, end_time, credentials):
    calendar_service = build('calendar', 'v3', credentials=credentials)

    event = {
        'summary': summary,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Asia/Tokyo',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Asia/Tokyo',
        },
    }
    event = calendar_service.events().insert(calendarId='primary', body=event).execute()
    print('Event created: %s' % (event.get('htmlLink')))

# ユーザーごとに認証情報を保存する関数
def save_credentials(author, credentials):
    filename = f'{author.id}_credentials.pickle'
    with open(filename, 'wb') as token:
        pickle.dump(credentials, token)

# ユーザーごとに保存された認証情報を読み込む関数
def load_credentials(author):
    filename = f'{author.id}_credentials.pickle'
    if os.path.exists(filename):
        with open(filename, 'rb') as token:
            return pickle.load(token)
    return None

# Discordコマンドを処理する関数
@bot.command()
async def schedule(ctx):
    await ctx.send('イベントのタイトルを入力してください。')

    def check_message(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        message = await bot.wait_for('message', timeout=120, check=check_message)
        summary = message.content

        await ctx.send('イベントの開始日時を年-月-日 時間:分形式で入力してください。例:2023―4―5 12:00')
        message = await bot.wait_for('message', timeout=120, check=check_message)
        start_time = message.content

        await ctx.send('イベントの終了日時を年-月-日 時間:分形式で入力してください。例:2023-4-5 15:00')
        message = await bot.wait_for('message', timeout=120, check=check_message)
        end_time = message.content

        credentials = load_credentials(ctx.author)
        if not credentials:
            credentials = await get_credentials(ctx.author)
            if not credentials:
                await ctx.send('認証エラーが発生しました。もう一度試してください。')
                return

        await create_event(ctx, summary, start_time, end_time, credentials)
        await ctx.send('イベントがカレンダーに追加されました！')

    except asyncio.TimeoutError:
        await ctx.send('タイムアウトしました。もう一度試してください。')

# ユーザーに認証を要求する関数
async def get_credentials(author):
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    await author.send(f'以下のリンクをクリックして認証してください: {authorization_url}')
    await author.send('認証が完了したら、取得したコードをこちらに入力してください。')

    try:
        message = await bot.wait_for('message', timeout=120, check=lambda m: m.author == author)
        flow.fetch_token(code=message.content)
        credentials = flow.credentials
        save_credentials(author, credentials)
        return credentials
    except asyncio.TimeoutError:
        await author.send('タイムアウトしました。もう一度試してください。')
        return None
    
#botがメッセージを受け取ったことを確認する関数
@bot.event
async def on_message(message):
    print(f'Message received: {message.content}')
    await bot.process_commands(message)

#botに登録されているコマンドを確認する関数
@bot.event
async def on_ready():
    print('Bot is ready!')
    print('Registered commands:')
    for command in bot.commands:
        print(command.name)

# ボットが準備完了したときに実行する関数
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

# Discordボットを起動する
bot.run(DISCORD_TOKEN)
