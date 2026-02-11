from flask import Blueprint, request, jsonify
from models.models import User
from extensions import db
import bcrypt
import re 
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

users_bp = Blueprint("users", __name__, url_prefix="/users")

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None



@users_bp.route("", methods=['POST'])
def createUser():
    dados = request.get_json(silent=True)

    if not dados:
        return jsonify({"msg":"JSON inválido"}), 400

    if not dados.get("username") or not dados.get("password") or not dados.get("email"):
        return jsonify({"msg":"Dados faltando"}), 400
    
    if not is_valid_email(dados.get("email")):
        return jsonify({"msg": "Email inválido"}), 400


    try: 
        password = dados.get("password")
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user = User(
            username = dados.get("username"),
            password_hash = hashed,
            email = dados.get("email")
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({"msg":"Usuário criado"}), 201
    
    except IntegrityError:
        db.session.rollback()
        return jsonify({"msg": "Usuário ou email já existente"}), 409

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"msg": "Erro no banco de dados"}), 500

    except Exception:
        db.session.rollback()
        return jsonify({"msg": "Erro inesperado"}), 500
    
@users_bp.route("/<int:id>", methods = ['GET'])
def getUser(id):
    response = db.get_or_404(User, id)
    print(response.id)
    return jsonify({"username": response.username, "email": response.email}), 201