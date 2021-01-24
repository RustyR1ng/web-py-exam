import os
import math

from flask import Flask, render_template, url_for, request, session, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

from mysql_db import MySQL
import mysql.connector as connector

app = Flask(__name__)
application = app
app.secret_key = os.urandom(24)
app.config.from_pyfile('config.py')

mysql = MySQL(app)


def query_ex(query, args, cursor, amount=None):
    cursor.execute(query, tuple(args))
    if (amount == 'one'):
        record = cursor.fetchone()
    elif (amount == 'many'):
        record = cursor.fetchmany()
    elif (amount == 'all'):
        record = cursor.fetchall()
    else:
        mysql.connection.commit()
    return record or None


from auth import bp as auth_bp, init_login_manager, check_rights

init_login_manager(app)
app.register_blueprint(auth_bp)

PER_PAGE = 10
MARKS = {
    0: "Ужасно",
    1: "Плохо",
    2: "Неудовлетворительно",
    3: "Удовлетворительно",
    4: "Хорошо",
    5: "Отлично"
}


@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    with mysql.connection.cursor(dictionary=True) as cursor:
        count = "SELECT count(*) AS count FROM films"
        total_pages = math.ceil(
            query_ex(count, [], cursor, 'one')['count'] / PER_PAGE)
        pagination_info = {
            'current_page': page,
            'total_pages': total_pages,
            'per_page': PER_PAGE
        }
        search_films = '''SELECT * FROM films
        ORDER BY year_of_production DESC
        LIMIT %s
        OFFSET %s;'''
        films = query_ex(search_films, [PER_PAGE, PER_PAGE * (page - 1)],
                         cursor, 'all')
        for film in films:
            search_genres = '''SELECT genre_name
            FROM film_genre
            JOIN genres ON genres.id = film_genre.genre WHERE film = %s'''
            genres = query_ex(search_genres, [film['id']], cursor, 'all')
            if genres:
                film['genres'] = [item['genre_name'] for item in genres]
            search_reviews = "SELECT count(*) AS count FROM reviews WHERE film = %s"
            reviews_a = query_ex(search_reviews, [film['id']], cursor, 'one')
            film['reviews_a'] = reviews_a['count']

    return render_template('films/index.html',
                           films=films,
                           pagination_info=pagination_info)


@app.route('/users/<int:user_id>')
@login_required
def show(user_id):
    with mysql.connection.cursor(named_tuple=True) as cursor:
        search_user = "SELECT * FROM users WHERE id = %s;"
        user = query_ex(search_user, [user_id], cursor, 'one')
        search_user_role = "SELECT * FROM roles WHERE id = %s;"
        role = query_ex(search_user_role, [user.role], cursor, 'one')
        search_user_reviews = '''SELECT films.film_name AS film, review, mark 
        FROM reviews 
        JOIN films ON films.id = reviews.film 
        WHERE user = %s'''
    with mysql.connection.cursor(dictionary=True) as cursor:
        reviews = query_ex(search_user_reviews, [user_id], cursor, 'all')
        if reviews:
            for i in range(len(reviews)):
                reviews[i]['mark'] = MARKS[reviews[i]['mark']]

    return render_template('users/show.html',
                           user=user,
                           role=role,
                           reviews=reviews)
