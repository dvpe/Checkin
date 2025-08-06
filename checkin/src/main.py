from flask import Flask, jsonify
import os
import logging
from logging.handlers import RotatingFileHandler
from config import Config
# Importe o nosso novo gerenciador
from models.database_manager import db_manager
from routes.campanhas_api import campanhas_bp
from routes.vans_api import vans_bp
from routes.checking_api import checking_bp
from routes.relatorios_api import relatorios_bp
# Importe o agendador
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Configurar logging
def configure_logging(app):
    # Garantir que o diretório de logs exista
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Configurar handler para arquivo
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    # Adicionar handlers ao logger do app
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Aplicação iniciada')

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configurar logging
    configure_logging(app)

    # Use o app_context para garantir que as configurações estejam disponíveis
    with app.app_context():
        # Inicializa nosso gerenciador de banco de dados
        db_manager.initialize(app)

    # Inicia o agendador para verificar a conexão do banco de dados
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        func=db_manager.schedule_reconnect_check,
        trigger='interval',
        minutes=5
    )
    scheduler.start()

    atexit.register(lambda: scheduler.shutdown())
    
    # Registrar blueprints
    app.register_blueprint(campanhas_bp, url_prefix='/api/campanhas')
    app.register_blueprint(vans_bp, url_prefix='/api/vans')
    app.register_blueprint(checking_bp, url_prefix='/api/checking')
    app.register_blueprint(relatorios_bp, url_prefix='/api/relatorios')
    
    # Rota para verificar saúde da aplicação
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0'
        })
    
    # Rota principal para documentação da API
    @app.route('/')
    def index():
        return jsonify({
            'mensagem': 'API de Gerenciamento de Campanhas de Publicidade',
            'documentacao': '/api/docs',
            'versao': '1.0.0'
        })
    
    # # Inicializar conexão com o banco de dados
    # @app.before_first_request
    # def initialize_db():
    #     try:
    #         Database.initialize()
    #         app.logger.info('Conexão com banco de dados inicializada')
    #     except Exception as e:
    #         app.logger.error(f'Erro ao inicializar banco de dados: {str(e)}')
    
    # Handler para erro 404
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            'erro': 'Recurso não encontrado',
            'status': 404
        }), 404
    
    # Handler para erro 500
    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f'Erro interno do servidor: {str(e)}')
        return jsonify({
            'erro': 'Erro interno do servidor',
            'status': 500
        }), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)