from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, OpenLink, EMPTY_KEYBOARD, Text
import psycopg2
from config import *
from random import choices
from api_model import User

db = psycopg2.connect(dbname=DB.db_name, user=DB.user, host=DB.host,password=DB.password)
sql = db.cursor()

bot = Bot(token)

def genCode(lenCode:int = 4):
    return ''.join(choices('1234567890qwertyuiopasdfgjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM', k=lenCode))


@bot.on.message(text=['login','Начать'])
async def message_handler(message:Message):
    sql.execute(f'SELECT COUNT(vk_id) FROM diary WHERE vk_id={message.from_id}')
    row = sql.fetchone()
    if row[0] == 0:
        keyboard = Keyboard(one_time=True)
        sql.execute(f'SELECT code FROM register WHERE user_id = {message.from_id}')
        code = sql.fetchone()
        code = code[0] if code else None
        if not code:
            code = genCode(6)
            sql.execute(f"INSERT INTO register (code, user_id) VALUES ('{code}',{message.from_id})")
            db.commit()

        keyboard.add(OpenLink(f'http://95.73.15.165/login?code={code}','Авторизация',payload={'auth':'hide'}),color=KeyboardButtonColor.NEGATIVE)

        await message.answer('Для работы с ботов авторизируйтесь через школьный портал!', keyboard=keyboard)
    else:
        keyboard = Keyboard().add(Text('Дз', payload={'event': 'homework'})).add(
            Text('Оценки', payload={'event': 'marks'})).add(Text('Расписание', payload={'event': 'lessons'}))
        await message.answer('Доступные действия', keyboard=keyboard)


@bot.on.message(payload={'auth':'hide'})
async def hide(message:Message):
    keyboard = Keyboard().add(Text('Дз',payload={'event':'homework'})).add(Text('Оценки',payload={'event':'marks'})).add(Text('Расписание',payload={'event':'lessons'}))
    await message.answer('Доступные действия',keyboard=keyboard)

@bot.on.message(text=['дз','ДЗ','Дз'])
@bot.on.message(payload={'event':'homework'})
async def message_handler(message:Message):
    sql.execute(f"SELECT * FROM diary WHERE vk_id = {message.from_id}")
    rows = sql.fetchone()
    if rows:
        await message.answer(User(rows[5]).lessons(_type=1))


@bot.on.message(text=['расписание','Расписание'])
@bot.on.message(payload={'event':'lessons'})
async def message_handler(message:Message):
    sql.execute(f"SELECT * FROM diary WHERE vk_id = {message.from_id}")
    rows = sql.fetchone()
    if rows:
        await message.answer(User(rows[5]).lessons())

@bot.on.message(text=['оценки','Оценки'])
@bot.on.message(payload={'event':'marks'})
async def message_handler(message:Message):
    sql.execute(f"SELECT * FROM diary WHERE vk_id = {message.from_id}")
    rows = sql.fetchone()
    if rows:
        await message.answer(User(rows[5]).get_marks())


bot.run_forever()

