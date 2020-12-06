import json
import smtplib
from random import *
import string
import hashlib

import os
from flask import Flask, render_template, request
app = Flask(__name__)
our_dir = os.path.dirname(os.path.abspath(__file__))
app.template_folder = os.path.join(our_dir, "templates")
username = ''


@app.route('/', methods=['post', 'get'])
def login():
    message = ''
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            if username is not None:
                email = check_login(username)
                if email == "":
                    return render_template('login.html', message="Пользователь не найден")
                onetime_pass = random_string()
                send_email(email, onetime_pass)
                save_hash(email, onetime_pass)
                save_username(username)
                return render_template('pass.html', message="Одноразовый пароль выслан на Ваш e-mail")
            elif password is not None:
                username = get_username()
                if compare_hashes(username, password):
                    return render_template('success.html', message=message)
                else:
                    return render_template('pass.html', message="Wrong password")

        except Exception as e:
            print(e)
    return render_template('login.html', message=message)


def check_login(username):
    with open("data.json") as datafile:
        my_json = json.load(datafile)
    for user in my_json['users']:
        if user['login'] == username:
            return user['email']
    return ""


def send_email(email, onetime_pass):
    FROM = "server333777@gmail.com"
    passwd = 'hCkeME5qZNWeuqf'
    TO = email
    SUBJECT = "Одноразовый пароль"
    TEXT = "Ваш одноразовый пароль:   " + onetime_pass
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
        """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(FROM, passwd)
        server.sendmail(FROM, TO, message)
        server.close()
        print('successfully sent the mail')
    except Exception as e:
        print(e)


def save_hash(email, onetime_pass):
    with open("data.json", 'r+') as datafile:
        my_json = json.load(datafile)
    for user in my_json['users']:
        if user['email'] == email:
            user['md5_hash'] = hashlib.md5(onetime_pass.encode()).hexdigest()
    with open("data.json", 'w') as datafile:
        json.dump(my_json, datafile)


def save_username(username):
    with open("current_user.txt", 'w') as file:
        file.write(username)


def get_username():
    with open("current_user.txt", 'r') as file:
        return file.read()


def compare_hashes(username, recieved_pass):
    with open("data.json", 'r') as datafile:
        my_json = json.load(datafile)
    for user in my_json['users']:
        if user['login'] == username:
            if user['md5_hash'] == hashlib.md5(recieved_pass.encode()).hexdigest():
                return True
            else:
                return False
    return False


def random_string():
    length = randint(7, 15)
    letters = string.ascii_lowercase
    result_str = ''.join(choice(letters) for i in range(length))
    return result_str



if __name__ == '__main__':
    app.run()
