import boto3
import os

# --- CONFIGURATION ---
TEMPLATE_NAME = "AnnualLeaveRejected"
HTML_FILE_PATH = "C:\\Users\\Dillon\\OneDrive\\Documents\\GitHub\\glad-pharmacy-chatbot\\email_templates\\annual_leave_rejected.html"
SUBJECT = "Your Annual Leave Was Rejected"

# --- Load HTML content ---
if not os.path.exists(HTML_FILE_PATH):
    raise FileNotFoundError(f"Could not find {HTML_FILE_PATH}")

with open(HTML_FILE_PATH, 'r', encoding='utf-8') as f:
    html_content = f.read()

# --- Create SES client ---
ses = boto3.client('ses', region_name='eu-west-2')  # Change region if needed

# --- Upload template ---
try:
    response = ses.create_template(
        Template={
            'TemplateName': TEMPLATE_NAME,
            'SubjectPart': SUBJECT,
            'HtmlPart': html_content,
            'TextPart': 'Your requested leave from {{start_date}} to {{end_date}} was rejected.'
        }
    )
    print("Template created successfully:", response)
except ses.exceptions.TemplateNameAlreadyExistsException:
    print(f"Template '{TEMPLATE_NAME}' already exists. Updating it...")
    response = ses.update_template(
        Template={
            'TemplateName': TEMPLATE_NAME,
            'SubjectPart': SUBJECT,
            'HtmlPart': html_content,
            'TextPart': 'Your requested leave from {{start_date}} to {{end_date}} was rejected.'
        }
    )
    print("Template updated successfully:", response)
