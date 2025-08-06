from flask import Blueprint
from .campanhas_api import campanhas_bp
from .vans_api import vans_bp
from .checking_api import checking_bp
from .relatorios_api import relatorios_bp

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Registrar os blueprints na API
api_bp.register_blueprint(campanhas_bp, url_prefix='/campanhas')
api_bp.register_blueprint(vans_bp, url_prefix='/vans')
api_bp.register_blueprint(checking_bp, url_prefix='/checking')
api_bp.register_blueprint(relatorios_bp, url_prefix='/relatorios')

# Definir rotas disponíveis para API
@api_bp.route('/', methods=['GET'])
def api_index():
    return {
        'status': 'success',
        'message': 'API de gerenciamento de campanhas publicitárias em vans escolares',
        'endpoints': {
            'campanhas': '/api/campanhas',
            'vans': '/api/vans',
            'checking': '/api/checking',
            'relatorios': '/api/relatorios'
        }
    }

def register_routes(app):
    """Registra as rotas da aplicação"""
    app.register_blueprint(api_bp)