"""入口:python -m server → 启动 Flask
后台启动:python scripts/daemon.py
"""
from .core import create_app
from . import config

app = create_app()


def main():
    print(f"🏗  MaterialWeb v{__import__('server').__version__}")
    print(f"   DB:        {config.DB_PATH}")
    print(f"   静态目录:  {config.STATIC_DIR}")
    print(f"   访问:      http://localhost:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)


if __name__ == '__main__':
    main()
