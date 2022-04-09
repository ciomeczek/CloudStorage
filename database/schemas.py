import marshmallow_sqlalchemy as ma
from .models import User, File, Directory


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        exclude = ("password",)


class DirectorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Directory
        load_instance = True

    files = ma.fields.Nested('FileSchema', many=True)
    children = ma.fields.Nested('DirectorySchema', many=True)


class FileSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = File
        load_instance = True
        exclude = ('directory',)
