from app import app, db

app_secret = os.environ['secret_key']
host = os.environ['host']
port = os.environ['port']

if __name__ == '__main__':
    handler = RotatingFileHandler('info.log',maxBytes=10000,backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.debug = True
    app.secret_key = app_secret
    app.run(host=host, port=int(port))
