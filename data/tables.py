from sqlalchemy     import Column, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import FromClause, func
from sqlalchemy.schema       import CreateColumn
from sqlalchemy.sql.schema   import ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP, Integer, TEXT, BOOLEAN
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.ext.asyncio  import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


from config import settings


#DATABASE_URL = "sqlite+aiosqlite:///database.db"


class BaseEngine:
    async_engine:  AsyncEngine = create_async_engine(settings.get_postegres_url, echo = True)
    async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(async_engine, expire_on_commit = False)


async def init_db():
    async with BaseEngine.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await BaseEngine.async_engine.dispose()


class Base(DeclarativeBase):
    ...
 

class User(Base):
    __tablename__ = 'users'

    id:         Mapped[Integer]    = mapped_column(Integer,    primary_key = True, autoincrement = "auto")
    first_name: Mapped[TEXT[50]]  = mapped_column(TEXT[50],  nullable = True)
    last_name:  Mapped[TEXT[50]]  = mapped_column(TEXT[50],  nullable = True)
    login:      Mapped[TEXT[50]]  = mapped_column(TEXT[50],  unique   = True, nullable = False)
    email:      Mapped[TEXT[100]] = mapped_column(TEXT[100], unique   = True, nullable = False)
    password:   Mapped[TEXT[200]]      = mapped_column(TEXT[200], nullable = False)
    description: Mapped[TEXT[500]] = mapped_column(TEXT[500], nullable=True)

    gratitudes: Mapped[list['Gratitude']] = relationship('Gratitude', back_populates = 'user')

class Gratitude(Base):
    __tablename__ = 'gratitudes'
    
    id:        Mapped[Integer]  = mapped_column(Integer,  primary_key = True, autoincrement = True)
    content:   Mapped[TEXT]    = mapped_column(TEXT,    nullable = False)
    image_url: Mapped[TEXT]    = mapped_column(TEXT,    nullable = True)
    is_public: Mapped[BOOLEAN] = mapped_column(BOOLEAN, default  = True)
    is_friend: Mapped[BOOLEAN] = mapped_column(BOOLEAN, server_default = "FALSE")
    user_id:   Mapped[Integer]  = mapped_column(Integer, ForeignKey(User.id))
    
    user:       Mapped['User']    = relationship('User',     back_populates = 'gratitudes')
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default = func.now())

class Friendship(Base):
    __tablename__ = 'friendships'
    
    id:             Mapped[Integer] = mapped_column(Integer, primary_key = True, autoincrement = True)
    user_id:        Mapped[Integer] = mapped_column(Integer, ForeignKey(User.id), nullable = False)
    friend_user_id: Mapped[Integer] = mapped_column(Integer, ForeignKey(User.id), nullable = False)
    
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default = func.now())

    user:   Mapped['User'] = relationship('User', foreign_keys = [user_id],        backref = 'friends')
    friend: Mapped['User'] = relationship('User', foreign_keys = [friend_user_id], backref = 'friend_of')

