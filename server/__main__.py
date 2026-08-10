"""入口:python -m server → 启动 Flask
后台启动:python scripts/daemon.py
"""
from .core import create_app
from . import config

app = create_app()


def main():
    reloader = 'on' if config.DEBUG else 'off'
    print(f"🏗  MaterialWeb v{__import__('server').__version__}")
    print(f"   DB:        {config.DB_PATH}")
    print(f"   静态目录:  {config.STATIC_DIR}")
    print(f"   访问:      http://localhost:{config.PORT}")
    print(f"   MW_DEBUG={1 if config.DEBUG else 0}, reloader={reloader}")
    # use_reloader 与 DEBUG 绑定:daemon detached 启动已强制 MW_DEBUG=0
    # 若前台调 python -m server 仍想开 reloader,MW_DEBUG=1 即可
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, use_reloader=config.DEBUG)


if __name__ == '__main__':
    main()
