#all backend api calls
import requests
from config import BACKEND_BASE_URL

def shorten_url(original_url: str):
    response = requests.post(
        f"{BACKEND_BASE_URL}/shorten",
        json = {"original_url":original_url}
    )
    return response

def get_stats(short_code: str):
    return requests.get(f"{BACKEND_BASE_URL}/stats/{short_code}")

def get_all_urls():
    return requests.get(f"{BACKEND_BASE_URL}/admin/urls")

def get_trending(top = 5):
    return requests.get(f"{BACKEND_BASE_URL}/admin/trending", params= {"top": top})