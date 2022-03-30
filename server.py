import os
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from entry import find_closest_date_form, clean_list_of_forms_by_date, extract_string_date, organize_form_submission_list, create_google_leads_excel_files
from jotform import *


app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

jotform_apikey = os.getenv("JOTFORM_APIKEY")
# globals
form_list = []


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/api/v1/get-date-range", methods=["POST"])
@cross_origin()
def get_date_range():
    data = request.get_json()
    start_date = data["start_date"]
    end_date = data["end_date"]

    jotformAPIClient = JotformAPIClient(jotform_apikey)
    forms = jotformAPIClient.get_forms(limit=50)
    start_form_date = find_closest_date_form(start_date, forms)
    end_form_date = find_closest_date_form(end_date, forms)

    cleaned_list_of_forms = clean_list_of_forms_by_date(
        start_date=extract_string_date(start_form_date['created_at']),
        end_date=extract_string_date(start_form_date['created_at']),
        forms_list=forms
    )

    return jsonify(cleaned_list_of_forms)
