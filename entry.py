from jotform import *
import os
import time
from dotenv import load_dotenv
from datetime import date
import xlsxwriter
import json

load_dotenv()

jotform_apikey = os.getenv("JOTFORM_APIKEY")


# objects for thrive and gf google leads submission
class GF_Google_Lead_Submission:
    '''
        gf_submission_info = {
            "submission_date": "2020-03-03",
            "fName": "John",
            "lName": "Smith",
            "email": "email@user.com".
            "phone": "1234567890",
            "zipcode": "12345",
            "utm_source": "google",
            "utm_medium": "cpc",
            "utm_campaign": "test",
            "utm_content": "test",
        }    
    '''

    def __init__(self, gf_submission_info):
        self.submission_date = gf_submission_info['submission_date']
        self.fName = gf_submission_info['fName']
        self.lName = gf_submission_info['lName']
        self.email = gf_submission_info['email']
        self.phone = gf_submission_info['phone']
        self.zipcode = gf_submission_info['zipcode']
        self.utm_source = gf_submission_info['utm_source']
        self.utm_medium = gf_submission_info['utm_medium']
        self.utm_campaign = gf_submission_info['utm_campaign']
        self.utm_content = gf_submission_info['utm_content']

    def clean_submission_info(self, form_name):
        '''
            clean up the submission info by adding values to the areas that are
            blank and by replacing certain values
        '''
        if self.utm_source == "attentive":
            self.utm_source = "sms"
        if self.utm_source == "listrak":
            self.utm_source = "email"
        if self.utm_source == "":
            self.utm_source = "website"
        if self.utm_medium == "":
            self.utm_medium = "org"
        if self.zipcode == "":
            self.zipcode = "77777"
        if self.utm_campaign == "":
            self.utm_campaign = ''.join(form_name.lower().split(" "))

        # check form title to find forms from GF Homepage
        sub_name = ""
        if len(form_name) > 7:
            sub_name = form_name[:7]
        if sub_name == "Home - ":
            temp_medium = self.utm_source
            temp_source = self.utm_medium
            self.utm_source = temp_source
            self.utm_medium = temp_medium

    def toJSON(self):
        return {
            "submission_date": self.submission_date,
            "fName": self.fName,
            "lName": self.lName,
            "email": self.email,
            "phone": self.phone,
            "zipcode": self.zipcode,
            "utm_source": self.utm_source,
            "utm_medium": self.utm_medium,
            "utm_campaign": self.utm_campaign,
            "utm_content": self.utm_content
        }


class Thrive_Google_Lead_Submission(GF_Google_Lead_Submission):
    '''
        thrive_submission_info = {
            "submission_date": "2020-03-03",
            "fName": "John",
            "lName": "Smith",
            "email": "email@user.com".
            "phone": "1234567890",
            "zipcode": "12345",
            "utm_source": "google",
            "utm_medium": "cpc",
            "utm_campaign": "test",
            "utm_content": "test",
            "utm_term": "test",
        }    
    '''

    def __init__(self, thrive_submission_info):
        super().__init__(thrive_submission_info)
        self.utm_term = thrive_submission_info['utm_term']

    def toJSON(self):
        return {
            "submission_date": self.submission_date,
            "fName": self.fName,
            "lName": self.lName,
            "email": self.email,
            "phone": self.phone,
            "zipcode": self.zipcode,
            "utm_source": self.utm_source,
            "utm_medium": self.utm_medium,
            "utm_campaign": self.utm_campaign,
            "utm_content": self.utm_content,
            "utm_term": self.utm_term
        }


'''
    date_start = "2020-03-04 00:00:00"
    returns = "2020-03-04"
'''


def extract_string_date(date_str):
    date_str = date_str.split(" ")
    return date_str[0]


'''
    start_date/end_date = "2020-10-04" <format of te date string>
'''


def find_interval_start_date(start_date, end_date):
    formatted_date1 = format_date(start_date)
    formatted_date2 = format_date(end_date)
    interval_days = substract_days(formatted_date1, formatted_date2)
    return interval_days


'''
    this function returns the number of days between two dates
'''


def substract_days(day1, day2):
    date1 = date(day1['year'], day1['month'], day1['day'])
    date2 = date(day2['year'], day2['month'], day2['day'])
    return abs((date1 - date2).days)


def format_date(date_str):
    formatted_date1 = time.strptime(date_str, "%Y-%m-%d")
    year = formatted_date1.tm_year
    month = formatted_date1.tm_mon
    day = formatted_date1.tm_mday
    return{"year": year, "month": month, "day": day}


def is_within_date_range(start_date, end_date, current_created_at_date, last_updated_date):
    if (current_created_at_date >= start_date and current_created_at_date <= end_date) or (last_updated_date >= start_date):
        return True
    else:
        return False


def organize_form_submission_list(form_submission_list, jotformAPIClient, startDate, endDate):
    cleaned_form_submission_data = {
        "gf": [],
        "thrive": []
    }
    gf_google_leads = []
    thrive_google_leads = []
    count = 0
    for form in form_submission_list:
        form_submissions = jotformAPIClient.get_form_submissions(
            form['id'], 0, 10000, {'created_at:gte': startDate, 'created_at:lte': endDate}, "created_at")
        for form_submission in form_submissions:
            form_answers = form_submission['answers']
            utm_content_key = find_key_in_dict(
                ['utm_content', 'utm_content'], form_answers)
            if utm_content_key == None:
                continue
            utm_content_obj = form_answers[utm_content_key]
            formLocation = utm_content_obj['answer'] if 'answer' in utm_content_obj else None
            form_submission_obj = create_form_submission_object(
                form_submission)
            if formLocation:
                if formLocation == "gf":
                    gf_google_lead_obj = GF_Google_Lead_Submission(
                        form_submission_obj)
                    gf_google_lead_obj.clean_submission_info(
                        form['title'])
                    gf_google_leads.append(gf_google_lead_obj)
                    count = count + 1
                elif formLocation.isdigit() or "thrive" in formLocation:
                    utm_term_key = find_key_in_dict(
                        ['utm_term', 'utm_term'], form_answers)
                    if 'answer' in form_submission['answers'][utm_term_key]:
                        form_submission_obj['utm_term'] = form_submission['answers'][utm_term_key]['answer']
                    else:
                        form_submission_obj['utm_term'] = ''
                    thrive_google_lead_obj = Thrive_Google_Lead_Submission(
                        form_submission_obj)
                    thrive_google_leads.append(thrive_google_lead_obj)
                    count = count + 1
            else:
                gf_google_lead_obj = GF_Google_Lead_Submission(
                    form_submission_obj)
                gf_google_lead_obj.clean_submission_info(
                    form['title'])
                gf_google_leads.append(gf_google_lead_obj)
                count = count + 1

    cleaned_form_submission_data['gf'].extend(gf_google_leads)
    cleaned_form_submission_data['thrive'].extend(thrive_google_leads)
    return cleaned_form_submission_data


def create_form_submission_object(form_submission):
    submission_info = {
        "submission_date": "",
        "fName": "",
        "lName": "",
        "email": "",
        "phone": "",
        "zipcode": "",
        "utm_source": "",
        "utm_medium": "",
        "utm_campaign": "",
        "utm_content": "",
    }

    # load the jotform_column_names.json file
    with open('jotform_column_names.json') as json_file:
        column_names = json.load(json_file)

        submission_info['submission_date'] = extract_string_date(
            form_submission['created_at'])
        answers_obj = form_submission['answers']
        submission_info['fName'] = get_value_from_answers(
            'firstName', answers_obj, column_names, False)
        submission_info['lName'] = get_value_from_answers(
            'lastName', answers_obj, column_names, False)
        submission_info['email'] = get_value_from_answers(
            'email', answers_obj, column_names, False)
        submission_info['phone'] = get_value_from_answers(
            'phoneNumber', answers_obj, column_names, True)
        submission_info['zipcode'] = get_value_from_answers(
            'zipCode', answers_obj, column_names, False)
        submission_info['utm_source'] = get_value_from_answers(
            'utm_source', answers_obj, column_names, False)
        submission_info['utm_medium'] = get_value_from_answers(
            'utm_medium', answers_obj, column_names, False)
        submission_info['utm_campaign'] = get_value_from_answers(
            'utm_campaign', answers_obj, column_names, False)
        utm_content_key = find_key_in_dict(
            column_names['utm_content'], answers_obj)
        if utm_content_key == None:
            submission_info['utm_content'] = 'gf'
        else:
            if 'answer' not in form_submission['answers'][utm_content_key]:
                submission_info['utm_content'] = 'gf'
            else:
                submission_info['utm_content'] = form_submission['answers'][utm_content_key]['answer']

    return submission_info


def get_value_from_answers(key, answers, column_names, isPhone):
    processed_key = find_key_in_dict(column_names[key], answers)
    if processed_key in answers:
        if isPhone:
            phone_answer = answers[processed_key]
            if 'prettyFormat' in phone_answer:
                return phone_answer['prettyFormat']
            else:
                return ""
        else:
            if 'answer' in answers[processed_key]:
                return answers[processed_key]['answer']
            else:
                return ""
    else:
        return ""


def create_google_leads_excel_files(google_leads_obj):
    gf_google_leads = google_leads_obj['gf']
    thrive_google_leads = google_leads_obj['thrive']
    create_google_leads_excel_file(gf_google_leads, filename="gf_google_leads")
    create_google_leads_excel_file(
        thrive_google_leads, filename="thrive_google_leads")
    return ("gf_google_leads.xlsx", "thrive_google_leads.xlsx")


def create_google_leads_excel_file(google_leads_list, filename):
    excel_sheet_name = filename + ".xlsx"
    create_excel_file(google_leads_list, excel_sheet_name)


def create_excel_file(google_leads_list, excel_sheet_name):
    google_leads_excel_file = xlsxwriter.Workbook(excel_sheet_name)
    google_leads_excel_sheet = google_leads_excel_file.add_worksheet()

    google_leads_excel_sheet.write(0, 0, "Submission Date")
    google_leads_excel_sheet.write(0, 1, "First Name")
    google_leads_excel_sheet.write(0, 2, "Last Name")
    google_leads_excel_sheet.write(0, 3, "Email")
    google_leads_excel_sheet.write(0, 4, "Phone")
    google_leads_excel_sheet.write(0, 5, "Zipcode")
    google_leads_excel_sheet.write(0, 6, "UTM Source")
    google_leads_excel_sheet.write(0, 7, "UTM Medium")
    google_leads_excel_sheet.write(0, 8, "UTM Campaign")
    google_leads_excel_sheet.write(0, 9, "UTM Content")
    if 'thrive' in excel_sheet_name:
        google_leads_excel_sheet.write(0, 10, "UTM Term")
    else:
        None

    last_row = 1

    for lead in google_leads_list:
        google_leads_excel_sheet.write(last_row, 0, lead.submission_date)
        google_leads_excel_sheet.write(last_row, 1, lead.fName)
        google_leads_excel_sheet.write(last_row, 2, lead.lName)
        google_leads_excel_sheet.write(last_row, 3, lead.email)
        google_leads_excel_sheet.write(last_row, 4, lead.phone)
        google_leads_excel_sheet.write(last_row, 5, lead.zipcode)
        google_leads_excel_sheet.write(last_row, 6, lead.utm_source)
        google_leads_excel_sheet.write(last_row, 7, lead.utm_medium)
        google_leads_excel_sheet.write(last_row, 8, lead.utm_campaign)
        google_leads_excel_sheet.write(last_row, 9, lead.utm_content)
        if 'thrive' in excel_sheet_name:
            google_leads_excel_sheet.write(last_row, 10, lead.utm_term)
        else:
            None
        last_row = last_row + 1
    google_leads_excel_file.close()


def find_key_in_dict(value, answer_dic):
    for k, v in answer_dic.items():
        if v['name'] == value[0] or value[0] in v['name'] or value[1] in v['name']:
            return k
    return None


def get_col_names_from_dict(answer_dic):
    names = []
    for k, v in answer_dic.items():
        names.append(v.get('name'))
    return names


def get_forms(startDate, jotform_client):
    jotforms = jotform_client.get_forms(
        0, 500, {'last_submission:gte': startDate}, "created_at")
    forms = []
    for form in jotforms:
        forms.append({
            'id': form['id'],
            'title': form['title'],
        })
    return forms


def main():

    jotformAPIClient = JotformAPIClient(jotform_apikey)

    iDate1 = input("Enter the start date in format YYYY-MM-DD: ")
    iDate2 = input("Enter the end date in format YYYY-MM-DD: ")

    iDate1 = iDate1 + " 00:00:00"
    iDate2 = iDate2 + " 23:59:59"

    forms = get_forms(iDate1, jotformAPIClient)

    organized_form_list = organize_form_submission_list(
        forms, jotformAPIClient, iDate1, iDate2)

    create_google_leads_excel_files(organized_form_list)


if __name__ == "__main__":
    main()