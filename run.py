import os

# Monkey patch ДО всех остальных импортов
try:
    from gevent import monkey
    monkey.patch_all()
    print("Gevent monkey patching applied successfully")
except Exception as e:
    print(f"Gevent monkey patching failed: {e}")
    # Fallback to threading
    os.environ['SOCKETIO_ASYNC_MODE'] = 'threading'
    
from app import create_app
from app.core.extensions import socketio

from dotenv import load_dotenv

load_dotenv('.env')

application = create_app()

print(f"Application created successfully: {application}")
print(f"SocketIO async_mode: {socketio.async_mode}")

if __name__ == '__main__':
     # Для development с gevent
    print(f"Starting Flask-SocketIO server with async_mode: {application.config.get('SOCKETIO_ASYNC_MODE', 'default')}")
    socketio.run(application, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
