import os
import re


from flask import Flask
from asgiref.wsgi import WsgiToAsgi
from werkzeug.middleware.proxy_fix import ProxyFix

from flask import render_template, jsonify, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash


from sqlalchemy.orm    import selectinload
from sqlalchemy.future import select
from sqlalchemy import func, or_


from config import settings

from data.tables       import BaseEngine, User, Friendship, Gratitude
from data.queries.user import (
    register_user, get_user_id, add_gratitude, 
    get_gratitudes, get_todays_gratitudes, get_gratitudes_by_method, 
    get_search_users, get_gratitudes_by_user_id, get_todays_gratitudes_by_user_id,
    get_user_stats, check_friendship, process_gratitude_date,
    update_user_description, get_user_description
)

from datetime import datetime
import pytz

app = Flask(__name__, template_folder = 'pages')
app.secret_key = settings.SECRET_KEY.get_secret_value()
app.wsgi_app = ProxyFix(app.wsgi_app)
asgi_app = WsgiToAsgi(app)

 
def is_valid_email(email):
    return re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email)

def is_valid_password(password):
    if len(password) < 8 or len(password) > 128:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if re.search(r'\s', password):
        return False
    if not re.match(r'^[a-zA-Zа-яА-Я0-9~!?@#$%^&*_\-\+\(\)\[\]\{\}><\/\\|"\'.,:;]+$', password):
        return False
    return True

def is_valid_login(login):
    return re.match(r'^[a-zA-Z0-9]+$', login)

def is_valid_name(name):
    return re.match(r'^[a-zA-Zа-яА-Я]*$', name)

@app.route('/')
async def index():
    user_id = session.get('user_id')
    friends_list = await get_friends(user_id) if user_id else []
    return render_template('index.html', friends=friends_list)


@app.route('/register', methods=['GET', 'POST'])
async def register():
    if 'user_id' in session:
            return redirect(url_for('index'))

    errors = {}
    general_error = None

    CHAR_LIMITS = {
        'first_name': 25,
        'last_name': 35,
        'login': 25,
        'email': 25,
        'password': 50
    }

    if request.method == 'GET':
        return render_template('register.html', errors=errors, form=request.form, CHAR_LIMITS=CHAR_LIMITS)

    first_name = request.form.get('first_name', '')
    last_name = request.form.get('last_name', '')
    login = request.form['login']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    # Проверка длины каждого поля
    if len(first_name) > CHAR_LIMITS['first_name']:
        errors['first_name'] = f"Ім'я не повинно перевищувати {CHAR_LIMITS['first_name']} символів!"
    
    if len(last_name) > CHAR_LIMITS['last_name']:
        errors['last_name'] = f"Прізвище не повинно перевищувати {CHAR_LIMITS['last_name']} символів!"
    
    if len(login) > CHAR_LIMITS['login']:
        errors['login'] = f"Логін не повинен перевищувати {CHAR_LIMITS['login']} символів!"
    
    if len(email) > CHAR_LIMITS['email']:
        errors['email'] = f"Пошта не повинна перевищувати {CHAR_LIMITS['email']} символів!"
    
    if len(password) > CHAR_LIMITS['password']:
        errors['password'] = f"Пароль не повинен перевищувати {CHAR_LIMITS['password']} символів!"

    if first_name and not is_valid_name(first_name):
        errors['first_name'] = 'Ім\'я повинно містити лише букви!'
    
    if last_name and not is_valid_name(last_name):
        errors['last_name'] = 'Прізвище повинно містити лише букви!'
    
    if not is_valid_login(login):
        errors['login'] = 'Логін повинен містити лише латинські букви та цифри, без пробілів!'
    
    if not is_valid_email(email):
        errors['email'] = 'Неправильний формат пошти!'
    
    if not is_valid_password(password):
        errors['password'] = 'Пароль не відповідає вимогам!'
    
    if password != confirm_password:
        errors['confirm_password'] = 'Паролі не співпадають!'

    if errors:
        general_error = 'Некоректні дані. Перевірте їх і повторіть спробу'
        return render_template('register.html', general_error=general_error, errors=errors, form=request.form, CHAR_LIMITS=CHAR_LIMITS)

    is_exist = await register_user(login, password, first_name, last_name, email)
    
    if is_exist:
        general_error = 'Користувач з таким логіном або електронною поштою вже існує!'
        return render_template('register.html', general_error=general_error, errors=errors, form=request.form, CHAR_LIMITS=CHAR_LIMITS)
    

    user_id = await get_user_id(login, password)  
    session['user_id'] = user_id 


    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
async def login_view():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    errors = {}
    invalid_credentials = False 

    if request.method == 'GET':
        return render_template('login.html', errors=errors, invalid_credentials=invalid_credentials)
    
    login = request.form.get('login')
    password = request.form.get('password')

    if not login:
        errors['login'] = 'Поле логина не может быть пустым'
    if not password:
        errors['password'] = 'Поле пароля не может быть пустым'

    if errors: 
        return render_template('login.html', errors=errors, invalid_credentials=invalid_credentials)
    
    user_id = await get_user_id(login, password)

    if user_id is not None:
        session['user_id'] = user_id

        return redirect(url_for('index'))
    
    invalid_credentials = True  
    flash('Неправильний логін або пароль!')
    return redirect(url_for('login_view'))


@app.route('/create', methods=['GET', 'POST'])
async def create_gratitude():
    user_id = session.get('user_id')
    if not user_id:
        flash('Спершу увійдіть до системи!', 'warning')  
        return redirect(url_for('login_view'))  

    if request.method == 'POST':

        today = datetime.now().date()
        async with BaseEngine.async_session() as db_session:
            gratitude_count = await db_session.execute(
                select(func.count())
                .select_from(Gratitude)
                .filter(
                    Gratitude.user_id == user_id,
                    Gratitude.created_at >= today
                )
            )
            count = gratitude_count.scalar()

        GRATITUDE_LIMIT = 3
        if count >= GRATITUDE_LIMIT:
            flash(f'Ви досягли ліміту в {GRATITUDE_LIMIT} подяк за день!', 'warning')
            return redirect(url_for('index'))

        content = request.form.get('content')
        image = request.files.get('image')
        gratitude_option = request.form.get('gratitude_option')
        is_public = gratitude_option == 'public'
        is_friend = gratitude_option == 'friend'
        image_url = None

        if image:
            image_folder = os.path.join('static', 'images')
            if not os.path.exists(image_folder):
                os.makedirs(image_folder)
            image_path = os.path.join(image_folder, image.filename)
            image.save(image_path)
            image_url = f'images/{image.filename}'

        await add_gratitude(
            content,
            image_url,
            is_public, 
            is_friend, 
            user_id
        )

        flash('Подяка створена!', 'success')  
        return redirect(url_for('index'))

    return render_template('index.html')  


@app.route('/global_gratitudes')
async def global_gratitudes():
    gratitudes = await get_gratitudes()  

    return render_template('global.html', gratitudes=gratitudes)


@app.route('/edit_profile', methods=['GET', 'POST'])
async def edit_profile():
    user_id = session.get('user_id')
    if not user_id:
        flash('Спершу увійдіть до системи!')
        return redirect(url_for('login_view'))

    async with BaseEngine.async_session() as db_session:
        user = await db_session.execute(select(User).filter_by(id=user_id))
        user = user.scalar_one_or_none()

        if not user:
            flash('Користувач не знайдений!')
            return redirect(url_for('index'))

        errors = {}
        if request.method == 'POST':
            current_password = request.form['current_password']
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            login = request.form.get('login', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()

            if not check_password_hash(user.password, current_password):
                errors['current_password'] = 'Неправильний поточний пароль!'

            if first_name and not is_valid_name(first_name):
                errors['first_name'] = 'Ім\'я повинно містити лише букви!'
            if last_name and not is_valid_name(last_name):
                errors['last_name'] = 'Прізвище повинно містити лише букви!'

            if not is_valid_login(login):
                errors['login'] = 'Логін повинен містити лише латинські букви та цифри, без пробілів!'
            else:
                existing_user = await db_session.execute(select(User).filter_by(login=login))
                existing_user = existing_user.scalar_one_or_none()
                if existing_user and existing_user.id != user.id:
                    errors['login'] = 'Такий логін уже використовується!'

            if not is_valid_email(email):
                errors['email'] = 'Неправильний формат пошти!'
            else:
                existing_user = await db_session.execute(select(User).filter_by(email=email))
                existing_user = existing_user.scalar_one_or_none()
                if existing_user and existing_user.id != user.id:
                    errors['email'] = 'Ця пошта вже використовується іншим користувачем!'

            if password:
                if not is_valid_password(password):
                    errors['password'] = 'Пароль не відповідає вимогам!'
                if password != confirm_password:
                    errors['confirm_password'] = 'Паролі не співпадають!'

            if not errors:
                user.first_name = first_name or user.first_name
                user.last_name = last_name or user.last_name
                user.login = login or user.login
                user.email = email or user.email
                if password:
                    user.password = generate_password_hash(password)

                db_session.add(user)
                await db_session.commit()

                flash('Зміни збережені!')

                return render_template('profile.html', user=user, errors=errors, success='Зміни збережені!')

        return render_template('profile.html', user=user, errors=errors)

async def get_friends(user_id):
    friends_list = []
    async with BaseEngine.async_session() as db_session:
        try:
            result = await db_session.execute(
                select(Friendship).filter(Friendship.user_id == user_id)
            )
            friendships = result.scalars().all()

            for friendship in friendships:
                friend_result = await db_session.execute(
                    select(User).filter(User.id == friendship.friend_user_id)
                )
                friend = friend_result.scalar_one_or_none()
                if friend:
                    friends_list.append(friend)
        except Exception as e:
            print(f"Ошибка при загрузке друзей: {e}")

    return friends_list


@app.before_request
async def load_friends():
    user_id = session.get('user_id')
    if user_id:
        g.friends = await get_friends(user_id)
    else:
        g.friends = []


@app.route('/friends', methods=['GET', 'POST'])
async def friends():
    user_id = session.get('user_id')
    if not user_id:
        flash('Спершу увійдіть до системи!')
        return redirect(url_for('login_view'))

    friends_list = await get_friends(user_id)

    if request.method == 'POST':
        nickname = request.form['nickname'].strip()
        async with BaseEngine.async_session() as db_session:
            try:
                result = await db_session.execute(select(User).filter_by(login=nickname))
                friend = result.scalar_one_or_none()

                if friend:
                    if friend.id == user_id:
                        return redirect(url_for('user_profile', user_id=user_id))
                    else:
                        return redirect(url_for('user_profile', user_id=friend.id))
                else:
                    flash('Користувача не знайдено!')
            except Exception as e:
                flash('Виникла помилка при пошуку користувача.')

    return render_template('friends.html', friends=friends_list)

@app.route('/profile', methods=['GET', 'POST'])
async def profile():
    user_id = session.get('user_id')
    if not user_id:
        flash('Спершу увійдіть до системи!')
        return redirect(url_for('login_view'))

    user_description = await get_user_description(user_id)

    if request.method == 'POST':
        description = request.form.get('description')
        if description:
            await update_user_description(user_id, description)
            flash('Опис успішно оновлено!', 'success')
            user_description = description 
        else:
            flash('Помилка при оновленні опису.', 'error')

    data = await get_todays_gratitudes(user_id)
    if data is None:
        flash('Користувача не знайдено!')
        return redirect(url_for('index'))

    todays_gratitudes, user = data
    friends_count, gratitudes_count = await get_user_stats(user_id)

    return render_template(
        'profile.html', 
        user=user, 
        todays_gratitudes=todays_gratitudes,
        friends_count=friends_count,
        gratitudes_count=gratitudes_count,
        user_description=user_description 
    )


@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
async def user_profile(user_id):
    current_user_id = session.get('user_id')
    if not current_user_id:
        flash('Спершу увійдіть до системи!')
        return redirect(url_for('login_view'))

    async with BaseEngine.async_session() as db_session:
        result = await db_session.execute(select(User).filter_by(id=user_id))
        user = result.scalar()

    if user is None:
        flash("Користувач не знайдений.")
        return redirect(url_for('feed'))

    is_friend = await check_friendship(current_user_id, user_id)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    gratitudes = await get_todays_gratitudes_by_user_id(user_id, today)

    gratitudes.sort(key=lambda x: x.created_at, reverse=True)

    for gratitude in gratitudes:
        process_gratitude_date(gratitude)
    
    friends_count, gratitudes_count = await get_user_stats(user_id)

    return render_template('user_profile.html', user=user, gratitudes=gratitudes,
                           friends_count=friends_count, gratitudes_count=gratitudes_count,
                           is_friend=is_friend)

@app.route('/search_users')
async def search_users():
    query = request.args.get('query', '').strip()
    users = await get_search_users(query)

    _json = [
        {
            'id':    user.id, 
            'login': user.login
        } for user in users
    ]
    return jsonify(_json)

@app.route('/feed')
async def feed():
    user_id = session.get('user_id')
    if not user_id:
        flash('Спершу увійдіть до системи!')
        return redirect(url_for('login_view'))

    gratitudes = await get_gratitudes_by_user_id(user_id)

    return render_template('feed.html', gratitudes=gratitudes)

@app.route('/archive')
async def archive():
    user_id = session.get('user_id')
    if not user_id:
        flash('Спершу увійдіть до системи!')
        return redirect(url_for('login_view'))

    async with BaseEngine.async_session() as db_session:
        gratitude_entries = await db_session.execute(
            select(Gratitude).options(selectinload(Gratitude.user)).filter_by(user_id=user_id).order_by(Gratitude.created_at.desc())
        )
        all_gratitudes = gratitude_entries.scalars().all()

        for gratitude in all_gratitudes:
            process_gratitude_date(gratitude)

    return render_template('archive.html', user_gratitudes=all_gratitudes)


@app.route('/gratitudes/<date>', methods=['GET'])
async def gratitudes_by_date(date):
    user_id = session.get('user_id')
    if not user_id:
        flash('Спершу увійдіть до системи!')
        return redirect(url_for('login_view'))

    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        flash('Неправильний формат дати! Використовуйте YYYY-MM-DD.')
        return redirect(url_for('profile'))

    todays_gratitudes = await get_todays_gratitudes_by_user_id(user_id, selected_date)

    return render_template('gratitudes_by_date.html', gratitudes=todays_gratitudes, selected_date=selected_date)

@app.route('/delete_friend/<int:friend_id>', methods=['POST'])
async def delete_friend(friend_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 403

    async with BaseEngine.async_session() as db_session:
        friendship = await db_session.execute(
            select(Friendship).filter_by(user_id=user_id, friend_user_id=friend_id)
        )
        friendship = friendship.scalar_one_or_none()

        if friendship:
            await db_session.delete(friendship)
            await db_session.commit()
            return jsonify({'success': True}), 200

        return jsonify({'error': 'Friend not found'}), 404
    
@app.route('/logout', methods=['POST'])
def logout():
    user_id = session.pop('user_id', None)  
    if user_id is not None:
        flash('Ви успішно вийшли з акаунту!', 'info')
    else:
        flash('Ви вже вийшли з акаунту.', 'info')
    return redirect(url_for('login_view'))


@app.route('/delete_gratitude/<int:gratitude_id>', methods=['POST'])
async def delete_gratitude(gratitude_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 403

    async with BaseEngine.async_session() as db_session:
        gratitude = await db_session.execute(
            select(Gratitude).filter_by(id=gratitude_id, user_id=user_id)
        )
        gratitude = gratitude.scalar_one_or_none()

        if gratitude:
            await db_session.delete(gratitude)
            await db_session.commit()
            return jsonify({'success': True}), 200

        return jsonify({'error': 'Gratitude not found'}), 404
    
@app.route('/friends_gratitudes')
async def friends_gratitudes():
    user_id = session.get('user_id')
    if not user_id:
        flash('Спершу увійдіть до системи!')
        return redirect(url_for('login_view'))

    async with BaseEngine.async_session() as db_session:
        friendships = await db_session.execute(
            select(Friendship).filter_by(user_id=user_id)
        )
        friend_ids = [friendship.friend_user_id for friendship in friendships.scalars().all()]

        gratitudes = await db_session.execute(
            select(Gratitude)
            .filter(Gratitude.user_id.in_(friend_ids))
            .filter(or_(Gratitude.is_public == True, Gratitude.is_friend == True))
            .options(selectinload(Gratitude.user))
            .order_by(Gratitude.created_at.desc())
        )
        gratitudes = gratitudes.scalars().all()

        for gratitude in gratitudes:
            process_gratitude_date(gratitude)

    return render_template('global.html', gratitudes=gratitudes)


@app.route('/update_profile_description', methods=['POST'])
async def update_profile_description():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Користувач не знайдений!'}), 404

    data = request.get_json()
    if not data or 'description' not in data:
        return jsonify({'error': 'Опис не може бути пустим.'}), 400

    description = data['description']

    try:
        await update_user_description(user_id, description)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

