from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from lightniwa import app

engine = create_engine(app.config['DATABASE_URI'],
                       convert_unicode=True,
                       **app.config['DATABASE_CONNECT_OPTIONS'])
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))


def init_db():
    Model.metadata.create_all(bind=engine)


Model = declarative_base(name='Model')
Model.query = db_session.query_property()


class Article(Model):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    cover = Column(String(255))
    content = Column(String())
    tags = Column(String(255))
    category_id = Column(Integer)
    create_user_id = Column(Integer)
    create_time = Column(Integer)
    view = Column(Integer, default=0)
    like = Column(Integer, default=0)

    def __init__(self, title, content):
        self.title = title
        self.content = content

    def to_json(self):
        return dict(title=self.title, content=self.content)


class User(Model):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(255))
    email = Column(String(255))
    phone = Column(String(255))
    password = Column(String(255))
    avatar = Column(String(255))
    level = Column(Integer)

    def is_active(self):
        return self.level > 0

    def is_authenticated(self):
        return self.level > 0

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def to_json(self):
        return dict(title=self.title, content=self.content)


class Anime(Model):
    __tablename__ = 'anime'
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer)
    month = Column(Integer)

    def to_json(self):
        return dict(id=self.id,
                    book_id=self.book_id,
                    month=self.month)


class Book(Model):
    __tablename__ = 'book'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    author = Column(String(255))
    illustrator = Column(String(255))
    publisher = Column(String(255))
    cover = Column(String(255))

    def __init__(self, id):
        self.id = id

    def to_json(self):
        return dict(id=self.id,
                    name=self.name,
                    author=self.author,
                    illustrator=self.illustrator,
                    publisher=self.publisher,
                    cover=self.cover)


class Volume(Model):
    __tablename__ = 'volume'
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer)
    name = Column(String(255))
    index = Column(String(255))
    description = Column(String(255))
    update_time = Column(String(255))
    cover = Column(String(255))
    click = Column(Integer)
    download = Column(Integer)

    def to_json(self):
        return dict(id=self.id,
                    book_id=self.book_id,
                    name=self.name,
                    index=self.index,
                    description=self.description,
                    update_time=self.update_time,
                    cover=self.cover,
                    click=self.click,
                    download=self.download)


class Chapter(Model):
    __tablename__ = 'chapter'
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer)
    vol_id = Column(Integer)
    name = Column(String(255))
    content = Column(String)
    update_by = Column(String(255))
    update_time = Column(String(255))
    file_path = Column(String(255))
    key = Column(String(255))
    view = Column(String(255))
    index = Column(String(255))

    def to_json(self):
        return dict(id=self.id,
                    book_id=self.book_id,
                    vol_id=self.vol_id,
                    name=self.name,
                    content=self.content,
                    update_by=self.update_by,
                    update_time=self.update_time,
                    file_path=self.file_path,
                    key=self.key,
                    view=self.view,
                    index=self.index)


class Count(Model):
    __tablename__ = 'download_ip'
    id = Column(Integer, primary_key=True)
    ip = Column(String(255))
    last_time = Column(Integer)
    frequency = Column(Integer)
    total = Column(Integer)


class Tag(Model):
    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))

    def to_json(self):
        return dict(id=self.id,
                    name=self.name,)
