from itertools import count
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS, cross_origin
from entry import get_forms, organize_form_submission_list_async, create_google_leads_excel_files
from jotform import *


app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

jotform_apikey = os.getenv("JOTFORM_APIKEY")
# globals
jotform_info = {
    "form_list": [],
    "start_date": "",
    "end_date": "",
    "organized_form_submissions": {
        "gf": [],
        "thrive": [],
    },
    "files": None,
}


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/api/v1/get-date-range", methods=["POST"])
@cross_origin()
def get_date_range():
    data = request.get_json()
    jotform_info['start_date'] = data["start_date"] + " 00:00:00"
    jotform_info['end_date'] = data["end_date"] + " 23:59:59"

    # reset jotform_info
    jotform_info["form_list"] = []
    jotform_info["organized_form_submissions"] = {
        "gf": [],
        "thrive": [],
    }
    jotform_info["files"] = None
    # remove xl files if they exists
    if os.path.exists("gf_google_leads.xlsx"):
        os.remove("gf_google_leads.xlsx")
    if os.path.exists("thrive_google_leads.xlsx"):
        os.remove("thrive_google_leads.xlsx")

    # # get form list from jotform
    jotformAPIClient = JotformAPIClient(jotform_apikey)
    jotform_info['form_list'] = get_forms(
        jotform_info['start_date'], jotformAPIClient)

    return jsonify(jotform_info['form_list'])


@app.route("/api/v1/get-forms-and-submissions", methods=["POST"])
@cross_origin()
def get_forms_and_submissions():
    data = request.get_json()
    organized_form_submission_list_obj = organize_form_submission_list_async(
        data['titles'], jotform_info['start_date'], jotform_info['end_date'])
    if len(jotform_info['organized_form_submissions']['gf']) != 0:
        jotform_info['organized_form_submissions']['gf'].clear()
        jotform_info['organized_form_submissions']['thrive'].clear()
    jotform_info['organized_form_submissions'] = organized_form_submission_list_obj
    serialed_form_submission_list = {
        "gf": [],
        "thrive": [],
    }
    for form_submission in organized_form_submission_list_obj['gf']:
        serialed_form_submission_list['gf'].append(form_submission.toJSON())
    for form_submission in organized_form_submission_list_obj['thrive']:
        serialed_form_submission_list['thrive'].append(
            form_submission.toJSON())
    return jsonify(serialed_form_submission_list)


@app.route("/api/v1/get-dates", methods=["GET"])
@cross_origin()
def get_dates():
    return jsonify({
        "start_date": jotform_info['start_date'],
        "end_date": jotform_info['end_date']
    })


@app.route("/api/v1/get-download-links", methods=["GET"])
@cross_origin()
def get_download_links():
    jotform_info['files'] = create_google_leads_excel_files(
        jotform_info['organized_form_submissions'])

    return jsonify({"files": [jotform_info['files'][0], jotform_info['files'][1]]})


@app.route("/gf_google_leads.xlsx", methods=["GET"])
@cross_origin()
def download_gf_excel():
    return send_file('gf_google_leads.xlsx', as_attachment=True)


@app.route("/thrive_google_leads.xlsx", methods=["GET"])
@cross_origin()
def download_thrive_excel():
    return send_file('thrive_google_leads.xlsx', as_attachment=True)
