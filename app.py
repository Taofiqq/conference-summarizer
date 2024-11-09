# from flask import Flask, request
# from twilio.twiml.voice_response import VoiceResponse, Dial
# from twilio.rest import Client
# import openai
# from sendgrid import SendGridAPIClient
# from dotenv import load_dotenv
# import os

# # Load environment variables
# load_dotenv()

# # Initialize Flask app
# app = Flask(__name__)

# # Configure API clients
# twilio_client = Client(
#     os.getenv('TWILIO_ACCOUNT_SID'),
#     os.getenv('TWILIO_AUTH_TOKEN')
# )
# openai.api_key = os.getenv('OPENAI_API_KEY')
# sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))

# # Basic route to test server
# @app.route('/')
# def home():
#     return 'Conference Summarizer Server is Running!'

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)
    

# @app.route('/join', methods=['POST'])
# def join_conference():
#     """Handle incoming calls and connect them to conference"""
#     print("New call received!")
    
#     # More detailed logging
#     print(f"Call SID: {request.values.get('CallSid')}")
#     print(f"From: {request.values.get('From')}")
#     print(f"To: {request.values.get('To')}")
#     response = VoiceResponse()
    
#     # Create Dial object
#     dial = Dial()
    
#     # Add caller to conference room named 'meeting_room'
#     dial.conference(
#         'meeting_room',
#         startConferenceOnEnter=True,
#         record='record-from-start',
#         recordingStatusCallback='/recording-status'
#     )
    
#     response.append(dial)
#     return str(response)

# @app.route('/recording-status', methods=['POST'])
# def recording_status():
#     """Handle recording status callbacks"""
#     recording_url = request.values.get('RecordingUrl')
#     recording_sid = request.values.get('RecordingSid')
    
#     # Store these values for later processing
#     # We'll implement processing in next step
#     print(f"Recording URL: {recording_url}")
#     print(f"Recording SID: {recording_sid}")
    
#     return 'OK'

from flask import Flask, request, jsonify
from twilio.twiml.voice_response import VoiceResponse, Dial, Gather
from twilio.rest import Client
import openai
from sendgrid import SendGridAPIClient
from dotenv import load_dotenv
import os
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure API clients
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)

openai.api_key = os.getenv('OPENAI_API_KEY')
sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

conference_recordings = {}

@app.route('/join', methods=['POST'])
def join_conference():
    try:
        
        logger.info("========= WEBHOOK RECEIVED - JOIN =========")
        logger.info(f"Caller: {request.values.get('From')}")
        logger.info(f"Request data: {request.values}")
        logger.info("====================================")
        
        response = VoiceResponse()
        gather = response.gather(numDigits=1, action='/process-gather')
        gather.say("Press any key to join the conference.")
        
        return str(response)
    except Exception as e:
        print("ERROR in join:", str(e))
        return str(e), 500

@app.route('/process-gather', methods=['POST'])
def process_gather():
    try:
        logger.info("========= CALLER JOINED CONFERENCE =========")
        logger.info(f"Caller: {request.values.get('From')}")
        logger.info("==========================================")
        
        
        response = VoiceResponse()
        dial = Dial()
        
        base_url = 'https://conference-summarizer.onrender.com'
        
        dial.conference(
            'meeting_room',
            startConferenceOnEnter=True,
            record='record-from-start',
          recordingStatusCallback='https://conference-summarizer.onrender.com/recording-status',
          recordingStatusCallbackEvent='in-progress completed',
          waitUrl='http://twimlets.com/holdmusic?Bucket=com.twilio.music.classical'
        )
        response.append(dial)
        return str(response)
    except Exception as e:
        print("ERROR in gather:", str(e))
        return str(e), 500

@app.route('/recording-status', methods=['POST'])
def recording_status():
    try:
        logger.info("========= RECORDING STATUS UPDATE =========")
        recording_data = {
            'url': request.values.get('RecordingUrl'),
            'sid': request.values.get('RecordingSid'),
            'status': request.values.get('RecordingStatus'),
            'duration': request.values.get('RecordingDuration'),
            'channels': request.values.get('RecordingChannels'),
            'source': request.values.get('RecordingSource'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store recording data
        conference_recordings[recording_data['sid']] = recording_data
        
        logger.info(f"Recording Status: {recording_data['status']}")
        logger.info(f"Recording URL: {recording_data['url']}")
        logger.info(f"Recording SID: {recording_data['sid']}")
        logger.info(f"Duration: {recording_data['duration']} seconds")
        
        # If recording is completed, we can process it
        if recording_data['status'] == 'completed':
            logger.info("Recording completed - ready for processing")
            # Here we'll add transcription logic later
        
        return 'OK'
    except Exception as e:
        logger.error(f"Error handling recording status: {str(e)}")
        return str(e), 500
    
@app.route('/recordings', methods=['GET'])
def list_recordings():
    """Debug endpoint to list all recordings"""
    return jsonify(conference_recordings)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('PORT', 5000))