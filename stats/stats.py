from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.models import Access, Site
from sqlalchemy import func
stats_bp = Blueprint("stats", __name__, url_prefix="/stats")

#Precisa de autenticação
#Precisa pegar a identidade
#Precisa pegar os sites do requerente
#Precisa retornar o número de acessos de cada site

@stats_bp.route("", methods=["GET"])
@jwt_required()
def returnSitesAcess():
    """
    Retorna as estatísticas de acesso das URLs do usuário autenticado
    ---
    tags:
      - Estatísticas
    security:
      - Bearer: []
    responses:
      200:
        description: Estatísticas retornadas com sucesso
        schema:
          type: array
          items:
            type: object
            properties:
              url_short:
                type: string
                example: "abc123"
              full_url:
                type: string
                example: "https://meusite.com/pagina-longa"
              access_count:
                type: integer
                example: 42
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

    results = db.session.execute(
        db.select(Site.url_short, Site. full_url, func.count(Access.id).label("access_count"))
        .outerjoin(Access, Site.url_short == Access.url_short)
        .filter(Site.user_id == identityInt)
        .group_by(Site.url_short, Site.full_url)
        .order_by(Site.full_url)
    )

    sites_list = [
        {
            "url_short": row.url_short,
            "full_url": row.full_url,
            "access_count": row.access_count
        }
        for row in results
    ]

    return jsonify(sites_list), 200

#d = db.session.query(Access).count()
#d = db.session.execute(db.select(Access).filter_by(url_short = short_url)).count()