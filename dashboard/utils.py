import requests
from django.conf import settings

def pin_donation_to_ipfs(donation_data):
    """
    Pins a JSON payload (e.g., donation data) to IPFS via Pinata.
    Returns the IPFS hash on success, or None on failure.
    """
    url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    headers = {
        "Content-Type": "application/json",
        "pinata_api_key": settings.PINATA_API_KEY,
        "pinata_secret_api_key": settings.PINATA_SECRET_API_KEY,
    }
    
    try:
        response = requests.post(url, json={"pinataContent": donation_data}, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        ipfs_hash = response.json().get("IpfsHash")
        return ipfs_hash
    except requests.RequestException as e:
        return None