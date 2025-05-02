import flask
import os

app = flask.Flask(__name__, static_folder='../static', template_folder='../templates')

@app.route('/')
def home():
    return flask.render_template('index.html')

@app.route('/vote')
def vote():
    return flask.render_template('vote.html')

@app.route('/blockchain')
def blockchain():
    return flask.render_template('blockchain.html')

@app.route('/results')
def results():
    return flask.render_template('results.html')

@app.route('/network')
def network():
    return flask.render_template('network.html')

if __name__ == '__main__':
    app.run(debug=True, port=5004)