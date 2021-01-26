import os
import math

from flask import Flask, render_template, url_for, request, session, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

from mysql_db import MySQL
import mysql.connector as connector

from markdown import markdown
from bleach import clean as bleach

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
        return
    return record


from auth import bp as auth_bp, init_login_manager, check_rights, load_record

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
def show_user(user_id):
    with mysql.connection.cursor(named_tuple=True) as cursor:
        user = load_record(user_id)
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
                           reviews=reviews,
                           markdown=markdown,
                           bleach=bleach)


@app.route('/films/<int:film_id>')
def show_film(film_id):
    with mysql.connection.cursor(named_tuple=True) as cursor:
        search_film = "SELECT * FROM films WHERE id = %s"
        film = query_ex(search_film, [film_id], cursor, 'one')
        search_genres = "SELECT genre_name FROM film_genre JOIN genres ON genres.id = film_genre.genre WHERE film = %s "
        genres = query_ex(search_genres, [film_id], cursor, 'all') or ''
    with mysql.connection.cursor(dictionary=True) as cursor:
        search_reviews = "SELECT users.id AS user_id, login, mark, review FROM reviews JOIN users ON users.id = reviews.user WHERE film = %s"
        current_u_review = None
        if current_user.is_authenticated:
            search_cur_review = search_reviews + " AND user = %s"
            current_u_review = query_ex(search_cur_review,
                                        [film_id, current_user.id], cursor,
                                        'one')
            if current_u_review:
                current_u_review['mark'] = MARKS[current_u_review['mark']]
        reviews = query_ex(search_reviews, [film_id], cursor, 'all') or ''
        for review in reviews:
            review['mark'] = MARKS[review['mark']]
    return render_template('films/show.html',
                           film=film,
                           reviews=reviews,
                           genres=', '.join(
                               [genre.genre_name for genre in genres]),
                           users_rev=[review['user_id'] for review in reviews],
                           u_review=current_u_review,
                           markdown=markdown,
                           bleach=bleach,
                           len=len)


@app.route('/films/review/<int:film_id>', methods=['GET', 'POST'])
@login_required
def review(film_id):
    with mysql.connection.cursor(named_tuple=True) as cursor:
        search_cur_review = "SELECT users.id AS user_id FROM reviews JOIN users ON users.id = reviews.user WHERE film = %s AND user = %s"
        reviewed = query_ex(search_cur_review, [film_id, current_user.id],
                            cursor, 'one')
        if reviewed:
            return redirect(url_for('show_film', film_id=film_id))
        if request.method == 'POST':
            form_data = request.form.values()
            insert_data = "INSERT INTO reviews (film,user,review, mark) VALUES(%s,%s,%s,%s)"
            try:
                query_ex(
                    insert_data,
                    [film_id, current_user.id, *[item for item in form_data]],
                    cursor)
                mysql.connection.commit()
            except connector.errors.DatabaseError as err:
                flash('Введены некорректные данные. Ошибка сохранения.',
                      'danger')
                return render_template('films/review.html', data=request.form)
            return redirect(url_for('show_film', film_id=film_id))
    return render_template('films/review.html')


def load_genres():
    with mysql.connection.cursor(named_tuple=True) as cursor:
        select_genres = "SELECT * FROM genres;"
        genres = query_ex(select_genres, [], cursor, 'all')
    return genres


@app.route('/films/form-create')
@login_required
@check_rights('create')
def form_create():
    return render_template('films/create.html', genres=load_genres(), film={})


@app.route('/films/create', methods=['POST'])
@login_required
@check_rights('create')
def create():
    form_data = {}
    for key, val in request.form.lists():
        if len(val) > 1:
            form_data[key] = [int(item) for item in val if item]
        else:
            form_data[key] = val[0] or None
    insert_film = '''INSERT INTO films (film_name, descrip, year_of_production, country, director, scenar, actors, duration_min)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s);'''
    insert_film_genres = '''INSERT INTO film_genre (film, genre)
        VALUES (%s,%s);'''
    with mysql.connection.cursor(named_tuple=True) as cursor:
        try:
            query_ex(insert_film, [
                form_data['film_name'], form_data['descrip'],
                form_data['year_of_production'], form_data['country'],
                form_data['director'], form_data['scenar'],
                form_data['actors'], form_data['duration_min']
            ], cursor)
            film_id = cursor.lastrowid
            for genre in form_data['genres']:
                query_ex(insert_film_genres, [film_id, genre], cursor)
            mysql.connection.commit()
        except connector.errors.DatabaseError as err:
            flash('Введены некорректные данные. Ошибка сохранения.', 'danger')
            return render_template('films/create.html',
                                   film=form_data,
                                   genres=load_genres())
    flash(f"Фильм {form_data['film_name']} был успешно создан", "success")
    return redirect(url_for('index'))


@app.route('/films/form-edit/<int:film_id>')
@login_required
@check_rights('edit')
def form_edit(film_id):
    with mysql.connection.cursor(dictionary=True) as cursor:
        search_film = "SELECT * FROM films WHERE id=%s;"
        film = query_ex(search_film, [film_id], cursor, 'one')
        search_film_genres = "SELECT genre FROM film_genre WHERE film=%s;"
        f_genres = query_ex(search_film_genres, [film_id], cursor, 'all')
        film['genres'] = [genre['genre'] for genre in f_genres]
        return render_template('films/edit.html',
                               genres=load_genres(),
                               film=film)


@app.route('/films/edit/<int:film_id>', methods=['POST'])
@login_required
@check_rights('edit')
def edit(film_id):
    form_data = {}
    for key, val in request.form.lists():
        if len(val) > 1:
            form_data[key] = [int(item) for item in val if item]
        else:
            form_data[key] = val[0] or None
    film_update = '''
        UPDATE films SET film_name=%s, descrip=%s, year_of_production=%s, country=%s, director=%s, scenar=%s, actors=%s, duration_min=%s
        WHERE id=%s;
    '''

    with mysql.connection.cursor(named_tuple=True) as cursor:
        try:
            query_ex(film_update, [
                form_data['film_name'], form_data['descrip'],
                form_data['year_of_production'], form_data['country'],
                form_data['director'], form_data['scenar'],
                form_data['actors'], form_data['duration_min'], film_id
            ], cursor)
            if form_data['genres']:
                genres_delete = "DELETE FROM film_genre WHERE film=%s"
                genres_update = "INSERT INTO film_genre (film, genre) VALUES (%s,%s) "
                query_ex(genres_delete, [film_id], cursor)
                for genre in form_data['genres']:
                    query_ex(genres_update, [film_id, genre], cursor)
            mysql.connection.commit()
        except connector.errors.DatabaseError as err:
            flash('Введены некорректные данные. Ошибка сохранения.', 'danger')
            return render_template('films/edit.html',
                                   film=form_data,
                                   genres=load_genres())
    flash(f"Фильм { form_data['film_name'] } был успешно обновлён.", "success")
    return redirect(url_for('index'))


@app.route('/films/delete/<int:film_id>', methods=['POST'])
@login_required
@check_rights('delete')
def delete(film_id):
    with mysql.connection.cursor(named_tuple=True) as cursor:
        try:
            delete_film = 'DELETE FROM films WHERE id=%s;'
            query_ex(delete_film, [film_id], cursor)
            mysql.connection.commit()
        except connector.errors.DatabaseError as err:
            flash('Не удалось удалить запись', 'danger')
            return redirect(url_for('index'))
        flash('Запись успешно удалена', 'success')
        return redirect(url_for('index'))


@app.route('/users/<int:user_id>/collections')
@login_required
def show_collections(user_id):
    if not current_user.can('collections', record=load_record(user_id)):
        flash('Вы не можете просмотреть подборки другого пользователя',
              'warning')
        return redirect(url_for('index'))
    with mysql.connection.cursor(dictionary=True) as cursor:
        page = request.args.get('page', 1, type=int)
        count = "SELECT count(*) AS count FROM collections"
        total_pages = math.ceil(
            query_ex(count, [], cursor, 'one')['count'] / PER_PAGE)
        pagination_info = {
            'current_page': page,
            'total_pages': total_pages,
            'per_page': PER_PAGE
        }
        search_collections = '''SELECT * FROM collections
        WHERE user=%s 
        LIMIT %s
        OFFSET %s;'''
        collections = query_ex(search_collections,
                               [user_id, PER_PAGE, PER_PAGE * (page - 1)],
                               cursor, 'all')
        search_films_amount = "SELECT COUNT(*) AS cnt FROM film_collection WHERE collection=%s"
        for collection in collections:
            films_amount = query_ex(search_films_amount, [collection['id']],
                                    cursor, 'one')
            collection['films_amount'] = films_amount['cnt']
        return render_template('users/collections.html',
                               collections=collections,
                               pagination_info=pagination_info)
