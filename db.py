from firebase_admin import credentials, firestore, storage
import firebase_admin
from datetime import datetime
import base64
import os

cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def new_position(position, start, end):
    start_object = datetime.strptime(start, '%Y-%m-%dT%H:%M')
    start_object = start_object.replace(second = 0)
    end_object = datetime.strptime(end, '%Y-%m-%dT%H:%M')
    end_object = end_object.replace(second = 0)
    start_timestamp = int(start_object.timestamp())
    end_timestamp = int(end_object.timestamp())

    new_entry = {
        'name': position,
        'start': start_timestamp,
        'end': end_timestamp,
        'applicants': {'NOTA':0},
        'voters': []
    }

    position = position.replace(" ", "_")
    position = position.lower()

    db.collection('positions').document(position).set(new_entry)

def new_applicant(position, name, email, desc):

    position = position.replace(" ", "_")
    position = position.lower()

    all_positions = all_available_positions_for_match()

    if position not in all_positions:
        return False

    encoded_image = image_to_base64()
    os.remove("image.png")

    new_entry = {
        'name': name,
        'desc': desc,
        'image': encoded_image,
        'email': email,
    }

    db.collection('applicants').document(email.split('@')[0]).set(new_entry)

    all_applicants = db.collection('positions').document(position).get()
    try:
        all_applicants = all_applicants.to_dict()['applicants']
    except:
        all_applicants = {}

    all_applicants[email.split('@')[0]] = 0
    db.collection('positions').document(position).update({'applicants': all_applicants})

def new_vote(position, userid, applicant):
    position = position.replace(" ", "_")
    position = position.lower()

    all_positions = all_available_positions_for_match()
    if position not in all_positions:
        return False

    all_voters = db.collection('positions').document(position).get()

    try:
        all_voters = all_voters.to_dict()['voters']
    except:
        all_voters = []

    if userid not in all_voters and applicant in aplicants_for_position(position):
        all_voters.append(userid)

        db.collection('positions').document(position).update({'voters': all_voters})

        all_applicants = db.collection('positions').document(position).get()
        all_applicants = all_applicants.to_dict()['applicants']
        all_applicants[applicant] += 1

        db.collection('positions').document(position).update({'applicants': all_applicants})

# To check total votes for a position
def all_voters(position):
    all_voters = db.collection('positions').document(position).get()
    return all_voters.to_dict()['applicants']


def all_votees(position):
    all_votees = db.collection('positions').document(position).get()
    return all_votees.to_dict()['voters']

# For dropdown in new position
def all_available_positions():
    all_positions = db.collection('positions').stream()
    all_positions = [doc.id for doc in all_positions]
    all_positions = [position.replace("_", " ").title() for position in all_positions]

    return all_positions


def all_available_positions_for_match():
    all_positions = db.collection('positions').stream()
    all_positions = [doc.id for doc in all_positions]
    return all_positions


def aplicants_for_position(position):
    position = position.replace(" ", "_")
    position = position.lower()

    all_applicants = db.collection('positions').document(position).get()
    all_applicants = all_applicants.to_dict()['applicants']

    return all_applicants

def positions_for_voter(userid):
    all_positions = db.collection('positions').stream()
    all_positions = [doc.id for doc in all_positions]
    all_positions = [position.replace("_", " ").lower() for position in all_positions]
    positions = []
    for position in all_positions:
        if userid not in all_votees(position):
            positions.append(position)

    return positions

# new_position('President', '2021-02-17 00:00:00', '2021-02-17 00:00:00', '2021')
# new_applicant('Presidehhhnt', 'Granth Bagadia', 'f20220217@hyderabad.bits-pilani.ac.in', 'None')
# new_vote('President', 'f20220211', 'f20220217')

def data_for_applicant(userid):
    applicant = db.collection('applicants').document(userid).get()
    applicant = applicant.to_dict()
    # applicant['image'] = applicant['image'].decode('utf-8')
    return applicant

def image_to_base64():
    with open("image.png", "rb") as image_file:
        image_data = image_file.read()
        base64_encoded = base64.b64encode(image_data).decode('utf-8')
    base64_encoded = "data:image/jpeg;base64," + base64_encoded
    return base64_encoded