from flask import jsonify, request, Blueprint
from flask_jwt_extended import create_access_token
from models.models import User
from extensions import db
import bcrypt

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route('', methods=['POST'])
def authHandler():
    dados = request.get_json(silent=True) 
    if not dados:
        return jsonify({"msg":"Dados invalidos"}),400
    
    if not dados.get("username") or not dados.get("password"): 
        return jsonify({"msg":"Dados faltando"}),400
    
    loginDate = {
        "username": dados.get("username"),
        "password": dados.get("password")
    }

    #GET USER BY USERNAME
    userStored = User.query.filter_by(username=dados["username"]).first()


    if not userStored:
        return jsonify({"msg": "Bad username or password"}), 401

    userData = {
        "id": userStored.id,
        "username": userStored.username,
        "hashedPassword": userStored.password_hash
    }

    if bcrypt.checkpw(loginDate["password"].encode('utf-8'), userData["hashedPassword"].encode('utf-8')):
        acess_token = create_access_token(
            identity=str(userData["id"]),
        )
        return jsonify({"access_token":acess_token}), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401
