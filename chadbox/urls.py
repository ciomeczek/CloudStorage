from chadbox import api
from chadbox import views

api.add_resource(views.UserView, "/users")
api.add_resource(views.TokenView, "/token")
api.add_resource(views.FileView, "/files", "/files/<path:path>")
api.add_resource(views.DirectoryView, "/directories/", "/directories/<path:path>")
