from app import create_app
import os
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app = create_app()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_ENV') == 'development')
