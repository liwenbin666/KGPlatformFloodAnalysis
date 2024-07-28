#view的配置
from applications.view.system import register_system_bp


def init_bp(app):
    # 各个模块蓝图的配置
    register_system_bp(app)