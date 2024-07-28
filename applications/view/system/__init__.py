from flask import Flask, Blueprint

from applications.view.system.Slice import bp as Slice
from applications.view.system.Feature import bp as Feature
from applications.view.system.FloodAnalysis import bp as FloodAnalysis
from applications.view.system.mdtw import bp as mdtw


system_bp = Blueprint('system', __name__, url_prefix='/pattern')


def register_system_bp(app: Flask):
    # # 继续添加bp
    system_bp.register_blueprint(Slice)
    # 最后将系统蓝图添加到app中
    app.register_blueprint(Feature)
    app.register_blueprint(FloodAnalysis)
    app.register_blueprint(system_bp)
    app.register_blueprint(Slice)
    app.register_blueprint(mdtw)

