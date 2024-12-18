import os
import requests
from flask import current_app
from pathlib import Path

class BreezeAPI:
    """Service for interacting with the Breeze ChMS API."""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('BREEZE_API_KEY')
        if not self.api_key:
            raise ValueError("Breeze API key not found")
        
        self.base_url = "https://refreshkc.breezechms.com/api"
        self.files_url = "https://files.breezechms.com"
        self.headers = {
            'Content-Type': 'application/json',
            'Api-Key': self.api_key
        }
    
    def get_members(self):
        """Fetch all members from Breeze."""
        response = requests.get(
            f"{self.base_url}/people",
            params={'details': '1'},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_member(self, member_id):
        """Fetch a specific member from Breeze."""
        response = requests.get(
            f"{self.base_url}/people/{member_id}",
            params={'details': '1'},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def update_member(self, member_id, data):
        """Update a member's information in Breeze."""
        response = requests.put(
            f"{self.base_url}/people/{member_id}",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

    def download_profile_image(self, image_path, save_dir):
        """
        Download a profile image from Breeze and save it locally.
        
        Args:
            image_path: The path of the image from Breeze (e.g., 'img/profiles/upload/65ec6d6b47ef2.jpg')
            save_dir: Directory to save the downloaded image
            
        Returns:
            The local path to the saved image, or None if download fails
        """
        if not image_path:
            return None
            
        try:
            # Create the save directory if it doesn't exist
            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Get the filename from the path
            filename = os.path.basename(image_path)
            save_path = save_dir / filename
            
            # Download the image
            response = requests.get(f"{self.files_url}/{image_path}", stream=True)
            response.raise_for_status()
            
            # Save the image
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return str(save_path)
            
        except Exception as e:
            current_app.logger.error(f"Error downloading profile image: {str(e)}")
            return None
