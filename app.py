import os
import pathlib
from flask import Flask, render_template, request, redirect, abort, session, url_for, jsonify
import requests
import cachecontrol
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import base64
from datetime import datetime

from db import new_position, new_applicant, all_available_positions, aplicants_for_position, positions_for_voter, data_for_applicant, new_vote

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
client_secrets_file = os.path.join(
    pathlib.Path(__file__).parent, "oauth.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri=os.getenv("CALLBACK")
)

@app.route('/login', methods=['GET', 'POST'])
def login():
    "DocString"
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    "DocString"
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(
        session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session['name'] = id_info['name']
    session['email'] = id_info['email']

    if 'bits-pilani.ac.in' not in id_info['email']:
        session.clear()
        return redirect("/")

    if 'f20220217' in session['email']:
        session['admin'] = True
    session['logged'] = True

    return redirect("/")

@app.route("/logout")
def logout():
    "DocString"
    session.clear()
    return redirect("/")


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'logged' not in session:
        return render_template('logout.html')
    else:
        if session['admin'] == False:
            return render_template('home.html')
        else:
            all_data = {}
            positions = positions_for_voter(session['email'].split('@')[0])
            if len(positions) == 0:
                return render_template('login.html', positions = positions, data = all_data)
            else:
                for i in positions:
                    all_data[i] = {}
                    applicants = aplicants_for_position(i)
                    all_data[i]['applicants'] = applicants
                    for j in applicants:
                        all_data[i][j] = data_for_applicant(j)
                return render_template('user.html', positions = positions, data = all_data)

@app.route('/new-position', methods=['GET', 'POST'])
def new_positions():
    if request.method == 'POST':
        position = request.form.get('position')
        start_timestamp = request.form.get('start')
        end_timestamp = request.form.get('end')
        new_position(position, start_timestamp, end_timestamp)

    return render_template('new_position.html')


@app.route('/new-applicant', methods=['GET', 'POST'])
def new_applicants():
    if request.method == 'POST':
        position = request.form.get('position')
        name = request.form.get('name')
        email = request.form.get('email')
        desc = request.form.get('desc')
        file = request.files['file']
        file.save("image.png")

        new_applicant(position, name, email, desc)

    return render_template('new_applicant.html', positions = all_available_positions())

@app.route('/vote/<position>/<userid>', methods=['GET', 'POST'])
def vote(position, userid):
    new_vote(position, session['email'].split('@')[0], userid)
    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True, port = 5000)