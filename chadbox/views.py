from flask import jsonify, make_response, send_from_directory
from flask import request
from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.models import User, Directory
from database.schemas import UserSchema, DirectorySchema
from chadbox import app
from database import db


class TokenView(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("email", type=str, required=True, help="Email is required")
        parser.add_argument("password", type=str, required=True, help="Password is required")
        args = parser.parse_args()

        email = args["email"]
        password = args["password"]

        user = User.get(email, password)

        if user is None:
            return make_response(jsonify({"message": "Invalid credentials"}), 401)

        access_token = create_access_token(identity=user.id)
        return make_response(jsonify({'access_token': access_token}), 200)


class UserView(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)

        return UserSchema().dump(user)

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("email", type=str, required=True, help="Email is required")
        parser.add_argument("password", type=str, required=True, help="Password is required")
        args = parser.parse_args()

        email = args["email"]
        password = args["password"]

        if not User.validate_email(email):
            return make_response(jsonify({"message": "Invalid email"}), 400)

        user = User.get(email)

        if user is not None:
            return make_response(jsonify({"message": "User already exists"}), 401)

        User(email, password)

        return make_response(jsonify({"message": "User created successfully"}), 201)


class FileView(Resource):
    @jwt_required()
    def get(self, path=None):
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)

        root = user.get_root_dir()
        file = root.get_file_by_path(path)

        if file is None:
            return make_response(jsonify({"message": f"File {path} does not exists"}), 404)

        return send_from_directory(app.config["UPLOAD_FOLDER"], path=file.filename, as_attachment=True)

    @jwt_required()
    def post(self, path=None):
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)

        root = user.get_root_dir()
        directory = root.get_dir_by_path(path)

        if directory is None:
            return make_response(jsonify({"message": f"Directory {path} does not exists"}), 400)

        for file in request.files.values():
            directory.add_file(file)

        return make_response(jsonify({"message": "Files uploaded successfully"}), 201)

    @jwt_required()
    def delete(self, path=None):
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)

        parser = reqparse.RequestParser()
        parser.add_argument("file_name", type=str, required=True, help="Filename is required")
        args = parser.parse_args()

        root = user.get_root_dir()
        directory = root.get_dir_by_path(path)

        if directory is None:
            return make_response(jsonify({"message": f"Directory {path} does not exists"}), 400)

        file_name = args["file_name"]
        file = directory.get_file_by_filename(file_name)

        if file is None:
            return make_response(jsonify({"message": f"File {file_name} does not exists. Ensure "
                                                     f"that the the filename is not the original filename"}), 400)

        directory.remove_file(file)

        return make_response(jsonify({"message": "File deleted successfully"}), 200)


class DirectoryView(Resource):
    @jwt_required()
    def get(self, path=None):
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)

        root_dir = user.get_root_dir()

        requested_dir = root_dir.get_dir_by_path(path)

        if requested_dir is None:
            return make_response(jsonify({"message": f"Directory or file {path} does not exists"}), 400)

        if requested_dir.author != user:
            return make_response(jsonify({"message": "You are not the owner of this directory"}), 401)

        return DirectorySchema().dump(requested_dir)

    @jwt_required()
    def post(self, path=None):
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)

        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, required=True, help="Name is required")
        args = parser.parse_args()

        directory_arg = args["name"]

        root = user.get_root_dir()
        directory = root.get_dir_by_path(path)

        if directory is None:
            return make_response(jsonify({"message": f"Directory {path} does not exists"}), 400)

        if directory.author != user:
            return make_response(jsonify({"message": "You are not the owner of this directory"}), 401)

        if directory.get_dir_by_name(directory_arg) is not None:
            return make_response(jsonify({"message": f"Directory {directory_arg} already exists"}), 400)

        new_dir = Directory(directory_arg, user, directory)
        new_dir.save()

        return make_response(jsonify({"message": "Directory created successfully"}), 201)

    @jwt_required()
    def delete(self, path=None):
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)

        root = user.get_root_dir()
        directory = root.get_dir_by_path(path)

        if directory is None:
            return make_response(jsonify({"message": f"Directory {path} does not exists"}), 400)

        if directory.author != user:
            return make_response(jsonify({"message": "You are not the owner of this directory"}), 401)

        db.session.delete(directory)
        db.session.commit()

        return make_response(jsonify({"message": "Directory deleted successfully"}), 204)
