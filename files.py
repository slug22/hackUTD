import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
URL = 'https://api.pinata.cloud/v3'
GROUP_ID = ''


JWT = os.getenv("PINATA_JWT")

if not JWT:
    raise ValueError("Environment variable PINATA_JWT is not set. Please check your .env file.")


def upload_question(question_data):
    HEADERS = {
        "Authorization": f"Bearer {JWT}",
        "Content-Type": "multipart/form-data"
    }

    payload = "test"

    try:
        response = requests.post(f'{URL}/files', headers=HEADERS, data=payload)
        response.raise_for_status()  # Raise HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to upload JSON: {e}")

# def retrieve_question_set():
#     HEADERS = {
#         "Authorization": f"Bearer {JWT}",
#     }
#
#     try:
#         response = requests.post(f"{URL}/", headers=HEADERS)
#         print(response.json())
#         response.raise_for_status()
#         # questions = []
#         # for row in response.json()["rows"]:
#         #     print(row)
#
#
#
#     except requests.exceptions.RequestException as e:
#         raise RuntimeError(f"Failed to retrieve question set: {e}")


# Testing
if __name__ == "__main__":
    # Define test JSON sample_data

    sample_data = {
        "description": "This is an example JSON object uploaded to Pinata.",
        "data": {
            "key1": "value1",
            "key2": "value2euaoeua",
            "nested": {
                "key3": "value3"
            }
        }
    }

    try:
        response = upload_question(sample_data)
        print(retrieve_question_set())
        print("JSON uploaded successfully:")
        print(response)
    except Exception as e:
        print(f"An error occurred: {e}")