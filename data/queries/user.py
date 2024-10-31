from sqlalchemy.sql import update, select, exists
from sqlalchemy.orm import selectinload
from sqlalchemy.engine.result import Sequence

from werkzeug.security import generate_password_hash, check_password_hash


from ..tables import BaseEngine, User, Gratitude, Friendship


from typing   import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from babel.dates import format_timedelta, format_datetime


async def register_user(login: str, password: str, first_name: str, last_name: str, email: str) -> bool:
    stmt = select(
        exists(1).
        where(User.login == login)
    )
    async with BaseEngine.async_session() as session:
        async with session.begin():
            result   = await session.execute(stmt)
            is_exist = result.scalar()

            if is_exist:
                return True

            kw = {
                User.first_name.key: first_name,
                User.last_name.key:  last_name,
                User.login.key:      login,
                User.email.key:      email,
                User.password.key:   generate_password_hash(password),
            }
            session.add(User(**kw))
            await session.commit()

    return False

async def get_user_id(login: str, password: str) -> Optional[int]:
    stmt = (
        select(User)
        .where(User.login == login)
    )
    async with BaseEngine.async_session() as db_session:
        async with db_session.begin():
            result = await db_session.execute(stmt)
            user = result.scalar()

    if user is not None and check_password_hash(user.password, password):
        return user.id

async def add_gratitude(
    content:   Optional[str],
    image_url: Optional[str],
    is_public: bool, 
    is_friend: bool, 
    user_id:   int
) -> None:
    kw = {
        Gratitude.content.key:   content,
        Gratitude.image_url.key: image_url,
        Gratitude.is_public.key: is_public,
        Gratitude.is_friend.key: is_friend,
        Gratitude.user_id.key:   user_id,
    }
    async with BaseEngine.async_session() as session:
        async with session.begin():
            session.add(Gratitude(**kw))
            await session.commit()


async def get_gratitudes() -> Sequence[Gratitude]:
    async with BaseEngine.async_session() as db_session:
        async with db_session.begin():
            result = await db_session.execute(
                select(Gratitude)
                .filter_by(is_public=True)
                .options(selectinload(Gratitude.user))
                .order_by(Gratitude.created_at.desc()) 
            )
            gratitudes = result.scalars().all()

            for gratitude in gratitudes:
                process_gratitude_date(gratitude)

            return gratitudes

async def get_todays_gratitudes(user_id: int) -> Optional[tuple[Sequence[Gratitude], User]]:
    async with BaseEngine.async_session() as db_session:
        user_result = await db_session.execute(
            select(User)
            .filter_by(id=user_id)
        )
        user = user_result.scalar()

        if user is None:
            return None

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        gratitude_entries = await db_session.execute(
            select(Gratitude)
            .filter_by(user_id=user_id)
            .filter(Gratitude.created_at >= today)
            .filter(Gratitude.created_at < tomorrow)
            .order_by(Gratitude.created_at.desc()) 
        )
        
        todays_gratitudes = gratitude_entries.scalars().all()

        for gratitude in todays_gratitudes:
            process_gratitude_date(gratitude)

        return todays_gratitudes, user

async def check_friendship(current_user_id: int, user_id: int) -> bool:
    async with BaseEngine.async_session() as db_session:
        existing_friendship = await db_session.execute(
            select(Friendship)
            .filter_by(user_id=current_user_id, friend_user_id=user_id)
        )
        return existing_friendship.scalar() is not None

async def get_gratitudes_by_method(method: str, current_user_id: int, user_id: int) -> tuple[User, Sequence[Gratitude], bool, str | None]:
    async with BaseEngine.async_session() as db_session:
        user = await db_session.execute(
            select(User)
            .filter_by(id=user_id)
        )
        user = user.scalar()

        if user is None:
            return 'Користувача не знайдено!', None, False, None

        gratitudes = await db_session.execute(
            select(Gratitude)
            .options(selectinload(Gratitude.user))
            .filter_by(user_id=user_id)
        )
        gratitudes = gratitudes.scalars().all()

        if method == 'POST':
            if current_user_id == user.id:
                return user, gratitudes, False, 'Ви не можете додати себе в друзі!'

            is_friend = await check_friendship(current_user_id, user_id)
            if is_friend:
                return user, gratitudes, is_friend, 'Користувач вже є у вашому списку друзів!'

            new_friendship = Friendship(user_id=current_user_id, friend_user_id=user.id)
            db_session.add(new_friendship)
            await db_session.commit()
            return user, gratitudes, True, 'Користувача додано до друзів!'

        return user, gratitudes, False, None


async def get_search_users(query: str) -> Sequence[User]:
    async with BaseEngine.async_session() as db_session:
        results = await db_session.execute(
            select(User).filter(User.login.ilike(f'%{query}%'))
        )
        return results.scalars().all()
    
async def get_gratitudes_by_user_id(user_id: int) -> Sequence[Gratitude]:
    async with BaseEngine.async_session() as db_session:
        friendships = await db_session.execute(
            select(Friendship.friend_user_id)
            .filter_by(user_id=user_id)
        )
        friend_ids = friendships.scalars().all()

        if not friend_ids:
            return []

        result = await db_session.execute(
            select(Gratitude)
            .filter(Gratitude.user_id.in_(friend_ids), Gratitude.is_public == True)
            .options(selectinload(Gratitude.user))
            .order_by(Gratitude.created_at.desc())
        )
        return result.scalars().all()


async def get_todays_gratitudes_by_user_id(user_id: int, selected_date: datetime) -> Sequence[Gratitude]:
    async with BaseEngine.async_session() as db_session:

        gratitude_entries = await db_session.execute(
            select(Gratitude).filter_by(user_id=user_id).filter(
                Gratitude.created_at >= selected_date,
                Gratitude.created_at < selected_date + timedelta(days=1) 
            )
        )
        return gratitude_entries.scalars().all()
    
async def get_user_stats(user_id):
    async with BaseEngine.async_session() as db_session:
        friends_count = await db_session.scalar(
            select(func.count())
            .select_from(Friendship)
            .filter_by(user_id=user_id)
        )

        gratitudes_count = await db_session.scalar(
            select(func.count())
            .select_from(Gratitude)
            .filter_by(user_id=user_id)
        )

    return friends_count, gratitudes_count

def process_gratitude_date(gratitude: Gratitude) -> None:
    if gratitude.created_at:

        local_timezone = timezone(timedelta(hours=2))

        local_created_at = gratitude.created_at.replace(tzinfo=timezone.utc).astimezone(local_timezone)
        time_difference = datetime.now(local_timezone) - local_created_at
        gratitude.humanized_created_at = format_timedelta(
            time_difference,
            locale='uk'
        ) + " тому"
        gratitude.full_date = format_datetime(local_created_at, locale='uk', format='d MMMM yyyy, HH:mm')
    else:
        gratitude.humanized_created_at = 'Дата недоступна'
        gratitude.full_date = 'Дата недоступна'

async def get_user_description(user_id: int) -> Optional[str]:
    async with BaseEngine.async_session() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user = result.scalar_one_or_none()
        
        if user:
            return user.description 
    return None 

async def update_user_description(user_id, description):
    async with BaseEngine.async_session() as session:
        user = await session.execute(select(User).filter_by(id=user_id))
        user = user.scalar_one_or_none()
        if user:
            user.description = description
            session.add(user)
            await session.commit()
