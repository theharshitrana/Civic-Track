from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_socketio import SocketIO

db = SQLAlchemy(engine_options={
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "pool_size": 20,
    "max_overflow": 10,
})

login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
cache = Cache()
socketio = SocketIO()

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))