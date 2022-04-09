from chadbox import app
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
from uuid import uuid4
from flask import abort
import os
import re


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __init__(self, email, password):
        self.email = email
        self.password = generate_password_hash(password)
        db.session.add(self)
        db.session.commit()

        Directory.create_root(self)
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get(email, password=None):
        user = User.query.filter_by(email=email).first()

        if not password:
            return user

        if user and check_password_hash(user.password, password):
            return user
        else:
            return None

    @staticmethod
    def get_by_id(user_id):
        user = User.query.filter_by(id=user_id).first()
        if not user:
            abort(401, "Invalid JWT")

        return user

    @staticmethod
    def validate_email(email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email)

    def get_root_dir(self):
        return Directory.query.filter_by(author=self, parent_id=None).first()


class Directory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('directories', lazy=True))
    parent_id = db.Column(db.Integer, db.ForeignKey('directory.id'))
    parent = db.relationship('Directory', backref=db.backref('children', lazy=True), remote_side=id)

    def __init__(self, name, author, parent=None):
        self.name = name
        self.author = author
        self.parent = parent

        db.session.add(self)
        db.session.commit()

    @staticmethod
    def create_root(author):
        if Directory.query.filter_by(author=author).first() is not None:
            return Directory.query.filter_by(author=author).first()

        directory = Directory(name='root', author=author)
        db.session.add(directory)
        db.session.commit()
        return directory

    def add_file(self, file):
        File(self.author, file, self)
        db.session.commit()

    def get_child(self, name):
        return Directory.query.filter_by(parent=self, name=name).first()

    def get_dir_by_name(self, name):
        return Directory.query.filter_by(parent=self, name=name).first()

    def get_file_by_filename(self, name):
        return File.query.filter_by(directory=self, filename=name).first()

    def get_dir_by_path(self, path):
        if path is None:
            return self

        directories = path.split('/')[:-1]
        filename = path.split('/')[-1]

        if filename != '':
            abort(404, f'{path} is a file')

        current_dir = self
        for directory in directories:
            current_dir = current_dir.get_child(directory)

            if current_dir is None:
                return None

        return current_dir

    def get_file_by_path(self, path):
        if path is None:
            return None

        directories = path.split('/')[:-1]
        directory_path = ''.join(directories)
        filename = path.split('/')[-1]

        if filename == '':
            abort(404, f'{path} is a directory')

        directory = self.get_dir_by_path(directory_path)

        if directory is None:
            return None

        return directory.get_file_by_filename(filename)

    def remove_file(self, file):
        if file not in self.files:
            return

        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

        db.session.delete(file)
        db.session.commit()


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # original filename is filename of file that user uploaded
    original_filename = db.Column(db.String(120), nullable=False)
    # not original filename is filename of file on a server
    filename = db.Column(db.String(120), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref=db.backref('files', lazy=True))
    directory_id = db.Column(db.Integer, db.ForeignKey('directory.id'))
    directory = db.relationship('Directory', backref=db.backref('files', lazy=True))

    def __init__(self, author, file, directory):
        self.original_filename = file.filename
        self.author = author
        self.filename = uuid4().__str__() + os.path.splitext(file.filename)[-1]
        self.directory = directory

        file.save(os.path.join(app.config["UPLOAD_FOLDER"], self.filename))

    def get_url(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], self.filename)
