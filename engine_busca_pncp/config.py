import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    dbname= os.getenv("DB_NAME")
    user= os.getenv("DB_USER")
    password= os.getenv("DB_PASSWORD")
    host= os.getenv("DB_HOST")
    port =os.getenv("DB_PORT")

    RESEND_API_KEY = os.getenv('RESEND_API_KEY')
    EMAIL_RESEND_FROM = os.getenv('EMAIL_FROM_RESEND')

    GMAIL_EMAIL_FROM=os.getenv('USER_GMAIL')
    GMAIL_PASSWORD=os.getenv('GMAIL_KEY')

    DEBUG = os.getenv('DEBUG', 'False') == 'True'




