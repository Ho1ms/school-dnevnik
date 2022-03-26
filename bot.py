from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, OpenLink, Text
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
    print('r',row)
    if row[0] == 0:
        keyboard = Keyboard()
        sql.execute(f'SELECT code FROM register WHERE user_id = {message.from_id}')
        code = sql.fetchone()
        if not code:
            code = genCode(6)
            sql.execute(f"INSERT INTO register (code, user_id) VALUES ('{code}',{message.from_id})")
            db.commit()
        else:
            code = code[0]
        print(code)
        keyboard.add(OpenLink(f'{server_url}login?code={code}','Авторизация'),color=KeyboardButtonColor.NEGATIVE)
        keyboard.add(Text('Функции',{'show':'func'}),color=KeyboardButtonColor.NEGATIVE)

        await message.answer('Для работы с ботов авторизируйтесь через школьный портал!\nПосле авторизации нажмите кнопку "Функции".', keyboard=keyboard.get_json())
    else:
        await message.answer('Вы уже авторизовались!')


@bot.on.message(payload={'auth':'hide'})
async def hide(message:Message):
    sql.execute(f"SELECT * FROM diary WHERE vk_id = {message.from_id}")
    rows = sql.fetchone()
    if rows:
        await message.answer('Вы успешно авторизовались')
        keyboard = Keyboard().add(Text('Дз',payload={'event':'homework'})).add(Text('Оценки',payload={'event':'marks'})).add(Text('Расписание',payload={'event':'lessons'}))
        await message.answer('Доступные действия',keyboard=keyboard.get_json())
    else:
        await message.answer('Вы ещё не прошли авторизацию!')

@bot.on.message(text=['дз','ДЗ','Дз'])
async def message_handler(message:Message):
    sql.execute(f"SELECT * FROM diary WHERE vk_id = {message.from_id}")
    rows = sql.fetchone()
    if rows:
        await message.answer(User(rows[5]).lessons(_type=1))


@bot.on.message(text=['расписание','Расписание'])
async def message_handler(message:Message):
    sql.execute(f"SELECT * FROM diary WHERE vk_id = {message.from_id}")
    rows = sql.fetchone()
    if rows:
        await message.answer(User(rows[5]).lessons())

@bot.on.message(text=['оценки','Оценки'])
async def message_handler(message:Message):
    sql.execute(f"SELECT * FROM diary WHERE vk_id = {message.from_id}")
    rows = sql.fetchone()
    if rows:
        await message.answer(User(rows[5]).get_marks())

@bot.on.message(text=['выход','loguot'])
async def message_handler(message:Message):
    sql.execute(f"DELETE FROM diary WHERE vk_id = {message.from_id}")
    db.commit()
    await message.answer('Вы успешно разлогинились!',keyboard=Keyboard().add(Text('Начать'),color=KeyboardButtonColor.NEGATIVE))


bot.run_forever()

