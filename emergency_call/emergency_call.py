from twilio.rest import Client
import os

def make_emergency_call():
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    to_number = os.getenv("EMERGENCY_PHONE_NUMBER")

    client = Client(account_sid, auth_token)

    call = client.calls.create(
    url='https://handler.twilio.com/twiml/EH9f749c43e700b69fdcb34e247961bbd2',  # replace with your TwiML Bin URL
    to=to_number,
    from_=from_number
)


    print(f"[EMERGENCY] Call initiated: {call.sid}")
    return call.sid
