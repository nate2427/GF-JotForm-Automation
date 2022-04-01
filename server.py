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
    "files": None
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

    jotformAPIClient = JotformAPIClient(jotform_apikey)
    jotform_info['form_list'] = get_forms(
        jotform_info['start_date'], jotformAPIClient)

    return jsonify(jotform_info['form_list'])


@app.route("/api/v1/get-forms-and-submissions", methods=["POST"])
@cross_origin()
def get_forms_and_submissions():
    organized_form_submission_list_obj = organize_form_submission_list_async(
        jotform_info['form_list'], jotform_info['start_date'], jotform_info['end_date'])
    if len(jotform_info['organized_form_submissions']['gf']):
        jotform_info['organized_form_submissions']['gf'].clear()
        jotform_info['organized_form_submissions']['thrive'].clear()
    print("got forms and submissions")
    for gf_form in organized_form_submission_list_obj['gf']:
        jotform_info['organized_form_submissions']['gf'].append(
            gf_form.toJSON())
    for thrive_form in organized_form_submission_list_obj['thrive']:
        jotform_info['organized_form_submissions']['thrive'].append(
            thrive_form.toJSON())
    return jsonify(jotform_info['organized_form_submissions'])


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
    if jotform_info['files'] == None:
        jotform_info['files'] = create_google_leads_excel_files(
            jotform_info['organized_form_submissions'])

    return jsonify({"files": [jotform_info['files'][0], jotform_info['files'][1]]})


@app.route("/gf_google_leads.xlsx", methods=["GET"])
@cross_origin()
def download_gf_excel():
    return send_file(jotform_info['files'][0], as_attachment=True)


@app.route("/thrive_google_leads.xlsx", methods=["GET"])
@cross_origin()
def download_thrive_excel():
    return send_file(jotform_info['files'][1], as_attachment=True)
