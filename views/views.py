import random
import string
from urllib.parse import urlparse
from flask import Blueprint
from flask import render_template, redirect, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models.models import Site, Access
from extensions import db

views_bp = Blueprint("views", __name__)

def generate_short_url(length=9):
    chars = string.ascii_letters + string.digits
    short_url = ""
    for n in range(length):
        short_url = short_url+random.choice(chars)
    
    return short_url

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


@views_bp.route("/url", methods=["POST"])
@jwt_required()
def createShortUrl():
    """
    Cria uma URL encurtada
    ---
    tags:
      - URLs
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - url
          properties:
            url:
              type: string
              example: "https://youtu.be/qivWOZsOPW0"
    responses:
      200:
        description: URL já encurtada anteriormente para este usuário
        schema:
          type: object
          properties:
            urlShortened:
              type: string
              example: "localhost:5000/abc123"
      201:
        description: URL encurtada criada com sucesso
        schema:
          type: object
          properties:
            urlShortened:
              type: string
              example: "localhost:5000/xyz789"
      400:
        description: Dados inválidos
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "URL inválida"
              enum:
                - "JSON inválido ou ausente"
                - "URL inválida"
                - "URL muito longa"
      401:
        description: Token ausente ou inválido
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Token has expired"
      409:
        description: Conflito ao gerar URL curta
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "URL curta já existente"
      500:
        description: Erro interno
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Erro inesperado"
              enum:
                - "Erro ao gerar URL curta única"
                - "Erro no banco de dados"
                - "Erro inesperado"
    """
    dados = request.get_json(silent=True)
    if not dados or not dados["url"]:
        return jsonify({"msg": "JSON inválido ou ausente"}), 400
    url = dados["url"]

    if not is_valid_url(url):
        return jsonify({"msg": "URL inválida"}), 400
    
    if len(url) > 2000:  # Limite razoável
        return jsonify({"msg": "URL muito longa"}), 400
    
    identity = get_jwt_identity() 
    identityInt = int(identity)

    siteCheck = db.session.execute(
            db.select(Site).filter_by(full_url=url, user_id=identityInt)
        ).scalar_one_or_none()

    if siteCheck:
        return jsonify({"urlShortened": request.host+request.root_path+"/"+siteCheck.url_short}), 200

    urlEncurtada = None
    for i in range(10):
        candidate = generate_short_url()
        siteStored = Site.query.filter_by(url_short = candidate).first()
        if not siteStored:
            urlEncurtada = candidate
            break
    
    if not urlEncurtada:
        return jsonify({"msg": "Erro ao gerar URL curta única"}), 500        

    try:
        site = Site(
            url_short = urlEncurtada,
            full_url = url,
            user_id = identityInt
        )

        db.session.add(site)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"msg": "URL curta já existente"}), 409

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"msg": "Erro no banco de dados"}), 500

    except Exception:
        db.session.rollback()
        return jsonify({"msg": "Erro inesperado"}), 500       

    return jsonify({"urlShortened": request.host+request.root_path+"/"+urlEncurtada}), 201  

@views_bp.route("/url/<short_url>", methods=["GET"])
@jwt_required()
def getUrl(short_url):
    """
    Busca uma URL pelo código curto
    ---
    tags:
      - URLs
    security:
      - Bearer: []
    parameters:
      - name: short_url
        in: path
        type: string
        required: true
        description: Código curto da URL
        example: "abc123"
    responses:
      200:
        description: URL encontrada
        schema:
          type: object
          properties:
            url:
              type: string
              example: "https://meusite.com/pagina-longa"
            shortCode:
              type: string
              example: "abc123"
      401:
        description: Token ausente ou inválido
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Token has expired"
      404:
        description: URL não encontrada
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Não encontrado"
    """
    siteStored = Site.query.filter_by(url_short = short_url).first()
    if not siteStored:
        return jsonify({"msg": "Não encontrado"}), 404
    
    return jsonify({"url": siteStored.full_url, "shortCode": siteStored.url_short})

@views_bp.route("/url", methods=["GET"])
@jwt_required()
def getUrls():
    """
    Lista todas as URLs encurtadas do usuário autenticado
    ---
    tags:
      - URLs
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de URLs retornada com sucesso
        schema:
          type: object
          additionalProperties:
            type: string
          example:
            "abc123": "https://meusite.com/pagina-longa"
            "xyz789": "https://outrosite.com/outra-pagina"
      401:
        description: Token ausente ou inválido
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Token has expired"
    """
    identity = get_jwt_identity()
    identityInt = int(identity)

    sites = db.session.execute(db.select(Site).filter_by(user_id = identityInt).order_by(Site.full_url)).scalars()
    sitesList = {}
    for item in sites:
        sitesList[item.url_short] = item.full_url
      
    return jsonify(sitesList),200

@views_bp.route("/url/<short_url>", methods=["PUT"])
@jwt_required()
def upadateUrl(short_url):
    """
    Atualiza a URL completa de um código curto existente
    ---
    tags:
      - URLs
    security:
      - Bearer: []
    parameters:
      - name: short_url
        in: path
        type: string
        required: true
        description: Código curto da URL a ser atualizada
        example: "abc123"
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - url
          properties:
            url:
              type: string
              example: "https://meusite.com/nova-pagina"
    responses:
      200:
        description: URL atualizada com sucesso
        schema:
          type: object
          properties:
            short_url:
              type: string
              example: "abc123"
            full_url:
              type: string
              example: "https://meusite.com/nova-pagina"
      400:
        description: Dados inválidos ou ausentes
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "JSON inválido ou ausente"
      401:
        description: Token ausente ou inválido
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Token has expired"
      403:
        description: Usuário não tem permissão para editar esta URL
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Forbidden"
      404:
        description: Código curto não encontrado
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Não encontrado"
      409:
        description: Erro de integridade no banco
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Erro de integridade"
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
    if not dados or not dados["url"]:
        return jsonify({"msg": "JSON inválido ou ausente"}), 400
    url = dados["url"]

    siteStored = Site.query.filter_by(url_short = short_url).first()
    if not siteStored: 
        return jsonify({"msg": "Não encontrado"}), 404
    identity = get_jwt_identity() 
    identityInt = int(identity)

    if siteStored.user_id != identityInt: 
        return jsonify({"msg": "Forbidden"}), 403
    
    try:
        siteStored.full_url = url
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"msg": "Erro de integridade"}), 409

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"msg": "Erro no banco de dados"}), 500

    except Exception:
        db.session.rollback()
        return jsonify({"msg": "Erro inesperado"}), 500   
    
    
    return jsonify({"short_url": siteStored.url_short, "full_url": url}),200


@views_bp.route("/url/<short_url>", methods=["DELETE"])
@jwt_required()
def deleteUrl(short_url):
    """
    Remove uma URL encurtada
    ---
    tags:
      - URLs
    security:
      - Bearer: []
    parameters:
      - name: short_url
        in: path
        type: string
        required: true
        description: Código curto da URL a ser removida
        example: "abc123"
    responses:
      200:
        description: URL removida com sucesso
      401:
        description: Token ausente ou inválido
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Token has expired"
      403:
        description: Usuário não tem permissão para remover esta URL
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Forbidden"
      404:
        description: URL não encontrada
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "URL não encontrada"
      409:
        description: Erro de integridade no banco
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Erro de integridade"
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
    siteStored = Site.query.filter_by(url_short = short_url).first()
    
    if not siteStored:
        return jsonify({"msg":"URL não encontrada"}), 404
    
    url = siteStored.full_url

    identity = get_jwt_identity()
    identityInt = int(identity)

    if siteStored.user_id != identityInt: 
        return jsonify({"msg": "Forbidden"}), 403

    try: 
        db.session.delete(siteStored)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"msg": "Erro de integridade"}), 409

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"msg": "Erro no banco de dados"}), 500

    except Exception:
        db.session.rollback()
        return jsonify({"msg": "Erro inesperado"}), 500  
    
    return jsonify({"msg": "Sucesso ao deletar URL","short_url": short_url, "full_url": url}),200
    

@views_bp.route("/<short_url>")
def redirect_url(short_url):
    siteStored = Site.query.filter_by(url_short = short_url).first()
    if not siteStored:
        return jsonify({"msg": "Não encontrado"}), 404
    
    try:
        acess = Access(
            url_short = siteStored.url_short,
            ip_address = request.remote_addr
        )

        db.session.add(acess)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        pass

    return redirect(siteStored.full_url, code=302)
