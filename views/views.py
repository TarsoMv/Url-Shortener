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

    tentativas = 10
    for i in range(tentativas):
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
    siteStored = Site.query.filter_by(url_short = short_url).first()
    if not siteStored:
        return jsonify({"msg": "Não encontrado"}), 404
    
    return jsonify({"url": siteStored.full_url, "shortCode": siteStored.url_short})

@views_bp.route("/url", methods=["GET"])
@jwt_required()
def getUrls():
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
    siteStored = Site.query.filter_by(url_short = short_url).first()
    url = siteStored.full_url
    if not siteStored:
        return jsonify({"msg":"URL nãzo encontrada"}), 404
    
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
    
    return jsonify({"msg": "Sucesso ao deletar URL","short_url": short_url, "full_url": url}),204
    

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