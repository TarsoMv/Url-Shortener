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
    """
    Registra um novo usuário
    ---
    tags:
      - Usuários
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
            - email
          properties:
            username:
              type: string
              example: "joao_silva"
            password:
              type: string
              format: password
              example: "senha123"
            email:
              type: string
              example: "joao@email.com"
    responses:
      201:
        description: Usuário criado com sucesso
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Usuário criado"
      400:
        description: Dados inválidos ou ausentes
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Dados faltando"
              enum:
                - "JSON inválido"
                - "Dados faltando"
                - "Email inválido"
      409:
        description: Usuário ou email já existente
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Usuário ou email já existente"
      500:
        description: Erro interno
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Erro inesperado"
              enum:
                - "Erro no banco de dados"
                - "Erro inesperado"
    """

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
    """
    Busca um usuário pelo ID
    ---
    tags:
      - Usuários
    deprecated: true
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID do usuário
        example: 1
    responses:
      201:
        description: Usuário encontrado
        schema:
          type: object
          properties:
            username:
              type: string
              example: "joao_silva"
            email:
              type: string
              example: "joao@email.com"
      404:
        description: Usuário não encontrado
    """
    response = db.get_or_404(User, id)
    print(response.id)
    return jsonify({"username": response.username, "email": response.email}), 201