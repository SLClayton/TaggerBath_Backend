from flask import Flask
import logging

app = Flask(__name__)
app.config["DEBUG"] = True




@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    logging.exception('An error occurred during a request.')
    return 'Sorry, nothing at this URL.', 404

@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500