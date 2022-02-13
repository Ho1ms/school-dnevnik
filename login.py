import flask
import json
from flask import render_template, request, url_for, make_response, redirect
from os import urandom, path, getcwd
from api_model import User
def dir(folder:str)->str:
    return path.join(getcwd(), folder)

app = flask.Flask('Login Manager', template_folder=dir('templates'), static_folder=dir('static'))


import psycopg2
from config import *

db = psycopg2.connect(dbname=DB.db_name, user=DB.user, host=DB.host,password=DB.password)
sql = db.cursor()

@app.route('/')
def main():
    code = request.cookies.get('code')

    if request.cookies.get('auth') or not code:
        return redirect(vk_url)

    print(request.url)

    return render_template('login.html', url=f'https://login.school.mosreg.ru/oauth2?response_type=token&client_id=bb97b3e445a340b9b9cab4b9ea0dbd6f&scope=CommonInfo,ContactInfo,FriendsAndRelatives,EducationalInfo&redirect_uri={request.url+url_for("main")}')

@app.route('/login')
def login():
    code = request.args.get('code')
    if code:
        print('login',type(code),code)
        res = make_response(redirect(url_for('main')))
        res.set_cookie('code', code)

        return res

@app.route('/api',methods=("POST",))
def api_handler():

    code = request.cookies.get('code')
    if code:
        res = make_response('Success', 200)
        res.set_cookie('auth', '1')

        token = json.loads(request.data.decode('utf-8')).get('token')
        print(code, token)

        sql.execute(f"SELECT user_id FROM register WHERE code = '{code}'")
        vk_id = sql.fetchone()
        print(vk_id)
        User(token).login(vk_id[0])
        sql.execute(f"DELETE FROM register WHERE code = '{code}'")
        db.commit()
        return res


if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0", port=80)