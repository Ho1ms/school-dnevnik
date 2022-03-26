import psycopg2
import json
import collections
import requests as req
from config import DB
import datetime

dateRussian = {
    'schedule' :['Января','Февраля','Марта','Апреля','Мая','Июня','Июля','Августа','Сентября','Октября','Ноября','Декабря'],
    'daysOfWeek':['Понедельник','Вторник','Среду','Четверг','Пятницу','Субботу','Воскресенье']
}

db = psycopg2.connect(dbname=DB.db_name, user=DB.user, host=DB.host,password=DB.password)
sql = db.cursor()

mainUrl = 'https://api.school.mosreg.ru/v2.0/'

class User:

    def __init__(self, token):
        self.token = token
        self.headers = {'Accept': 'application/json', 'Access-Token': token}

    def login(self, vkId: int):
        data = json.loads(req.get(mainUrl + 'users/me', headers=self.headers).text)
        print(data)
        infoGroup = req.get(mainUrl + f'persons/{data["personId"]}/edu-groups', headers=self.headers).text
        print(infoGroup)
        group_id = [group['id'] for group in json.loads(infoGroup) if group['type'] == 'Group'][0]

        infoSchool = req.get(mainUrl + 'schools/person-schools', headers=self.headers).text
        print(infoSchool)
        school_id = [school['id'] for school in json.loads(infoSchool) if school['educationType'] == 'Regular'][0]

        sql.execute(f'SELECT COUNT(vk_id) FROM diary WHERE vk_id = {vkId}')
        if not sql.fetchone()[0]:
            sql.execute(
                f"""INSERT INTO diary (vk_id,user_id,email,token_access,group_id, school_id) VALUES ({vkId},{data['personId']},'{data['email']}','{self.token}',{group_id}, {school_id})""")
            db.commit()

    def lessons(self, _type: int = 0, date: datetime.datetime = datetime.datetime.now()):
        sql.execute(f"SELECT user_id, group_id, school_id FROM diary WHERE token_access = '{self.token}'")
        rows = sql.fetchone()

        info = req.get(
            mainUrl + f'persons/{rows[0]}/groups/{rows[1]}/schedules?startDate={date}&endDate={date + datetime.timedelta(days=1)}',
            headers=self.headers).text

        data = json.loads(info)
        if data.get('type')=='invalidToken':
            return 'Ваш токен авторизации устарел, пройдите авторизацию снова!'
        data = data['days'][1:]
        lessons = []
        Date = self.date_parse(data[0]['date'])

        home_works = self.get_homework(rows[2], date) if _type else ()
        print(home_works)
        print(info)
        print(data)
        msg = f"Рассписание на {dateRussian['daysOfWeek'][Date.weekday()]} ({Date.day} {dateRussian['schedule'][Date.month - 1]})\n\n"
        for j, i in enumerate(data[0]['lessons']):

            for row in data[0]['subjects']:
                if row['id'] == i['subjectId']:
                    name = row['name']
                    break
            home = 'Не задано'
            for work in home_works:
                if work['lesson'] == i['id']:
                    home = work['text']
                    break

            if not _type:
                lessons.append((f"""{i["number"]}. {name} """ + f'[{i["place"]}]' or '', i["number"]))
            elif _type:
                print(i["place"], type(i["place"]))
                lessons.append((f'{i["number"]}. {name}'+ (f' [{i["place"]}]\n' if i["place"] else '\n') +f'• {home}\n', i["number"]))

        lessons.sort(key=lambda x: x[1])
        msg += ''.join([f'{lesson[0]}\n' for lesson in lessons]) or 'Нет уроков'

        return msg

    def get_homework(self, school_id: int, date: datetime.datetime = datetime.datetime.now()):
        info = req.get(mainUrl + f'users/me/school/{school_id}/homeworks', headers=self.headers,
                       params={'startDate': date, 'endDate': date + datetime.timedelta(days=1)})
        if info.status_code == 200:
            return json.loads(info.text).get('works')

    def report_period(self, date: datetime.datetime = datetime.datetime.now()):
        sql.execute(f"SELECT group_id FROM diary WHERE token_access = '{self.token}'")
        group_id = sql.fetchone()[0]

        r = req.get(mainUrl + f'edu-groups/{group_id}/reporting-periods', headers=self.headers)
        periods = json.loads(r.text)

        for period in periods:
            if self.date_parse(period['start']) <= date <= self.date_parse(period['finish']):
                break

        return period

    def date_parse(self, date: str) -> datetime.datetime:
        return datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')

    def get_marks(self):
        date = self.report_period()
        sql.execute(f"SELECT user_id,group_id,school_id FROM diary WHERE token_access = '{self.token}'")
        user_id, group_id, school_id = sql.fetchone()
        payload = []
        data_marks = {}
        lessons = json.loads(
            req.get(mainUrl + f'persons/{user_id}/schools/{school_id}/marks/{date["start"]}/{date["finish"]}',
                    headers=self.headers).text)

        for lesson in lessons:
            payload.append(lesson['lesson'])
            data_marks[lesson['lesson']] = int(lesson['value'])

        marks = sorted(json.loads(req.post(mainUrl + 'lessons/many', json=payload, headers=self.headers).text),
                       key=lambda x: x['date'])
        lessons_data = {}

        for mark in marks:
            name = mark['subject']['name']
            if name not in lessons_data:
                lessons_data[name] = []
            lessons_data[name].append(data_marks[int(mark['id_str'])])

        lessons = collections.OrderedDict(sorted(lessons_data.items()))

        msg = f'Ваши оценки за {date["name"]}:\n\n'

        for i, lesson in enumerate(lessons, start=1):
            avg_mark = sum(lessons[lesson]) / len(lessons[lesson])
            msg += f'{i}. {lesson}\n• {", ".join(map(str, lessons[lesson]))} [{round(avg_mark, 2)}]\n\n'

        return msg