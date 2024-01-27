import os
import pathlib
from flask import Flask, render_template, request, redirect, abort, session, url_for, jsonify
import requests
import cachecontrol
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests

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


@app.route('/')
def index():
    if 'logged' not in session:
        return render_template('logIn.html')
    else:
        if session['admin'] == True:
            return render_template('admin.html')
        else:
            return render_template('logOut.html')

if __name__ == '__main__':
    app.run(debug=True)