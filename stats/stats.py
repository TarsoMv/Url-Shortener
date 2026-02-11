from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.models import Access
stats_bp = Blueprint("stats", __name__, url_prefix="/stats")



#d = db.session.query(Access).count()
#d = db.session.execute(db.select(Access).filter_by(url_short = short_url)).count()