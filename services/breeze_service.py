import os
import json
import logging
import requests
from datetime import datetime
from typing import List, Dict, Optional

class BreezeAPI:
    BASE_URL = "https://refreshkc.breezechms.com/api"
    
    def __init__(self):
        self.api_key = os.getenv('BREEZE_API_KEY')
        if not self.api_key:
            raise ValueError("BREEZE_API_KEY environment variable is not set")
        self.headers = {
            'Content-Type': 'application/json',
            'Api-Key': self.api_key
        }
    
    def get_people(self) -> List[Dict]:
        """Fetch all people with detailed profile information from BreezeChMS"""
        try:
            # Get profile fields first
            profile_fields = self.get_profile_fields()
            field_ids = [field.get('id') for field in profile_fields if field.get('id')]
            
            # Get people with profile fields and include details
            params = {
                'details[]': field_ids,
                'include_inactive': 0,  # Only get active members
                'include_details': 1,  # Include all details
                'include_photos': 1  # Include photo URLs
            }
            response = requests.get(
                f"{self.BASE_URL}/people",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, bool):
                return []
            elif not isinstance(data, list):
                return [data] if data else []
            return data
        except Exception as e:
            print(f"Error fetching people with details: {str(e)}")
            return []
    
    def get_profile_fields(self) -> List[Dict]:
        """Fetch all profile fields from BreezeChMS"""
        logger = logging.getLogger(__name__)
        logger.info("Fetching profile fields from BreezeChMS")
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/profile",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"Received profile fields response: {data}")
            
            # Handle different response formats
            if isinstance(data, bool):
                logger.warning("Received boolean response for profile fields")
                return []
            elif isinstance(data, dict):
                logger.info("Received dictionary response, converting to list")
                return [data] if data else []
            elif isinstance(data, list):
                logger.info(f"Received {len(data)} profile fields")
                return data
            else:
                logger.warning(f"Unexpected response type: {type(data)}")
                return []
                
        except requests.Timeout:
            logger.error("Timeout while fetching profile fields")
            raise ValueError("Connection to BreezeChMS timed out")
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise ValueError(f"Failed to fetch profile fields: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise ValueError(f"Error processing profile fields: {str(e)}")
    def get_person(self, breeze_id: str) -> Optional[Dict]:
        """Fetch a specific person from BreezeChMS"""
        response = requests.get(
            f"{self.BASE_URL}/people/{breeze_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def update_person(self, breeze_id: str, data: Dict) -> Dict:
        """Update a person's information in BreezeChMS"""
        response = requests.put(
            f"{self.BASE_URL}/people/{breeze_id}",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_total_membership(self) -> int:
        """Get total number of active members"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/people",
                headers=self.headers,
                params={'filter_json': json.dumps({'status': 'active'})}
            )
            response.raise_for_status()
            return len(response.json())
        except Exception as e:
            print(f"Error fetching total membership: {str(e)}")
            return 0

    def get_baptisms_for_year(self, year: int) -> int:
        """Get number of baptisms for a specific year"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/events/baptisms",
                headers=self.headers,
                params={'year': year}
            )
            response.raise_for_status()
            return len(response.json())
        except Exception as e:
            print(f"Error fetching baptisms: {str(e)}")
            return 0

    def get_new_members_for_year(self, year: int) -> int:
        """Get number of new members for a specific year"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/people",
                headers=self.headers,
                params={
                    'filter_json': json.dumps({
                        'membership_date': {
                            'start': f"{year}-01-01",
                            'end': f"{year}-12-31"
                        }
                    })
                }
            )
            response.raise_for_status()
            return len(response.json())
        except Exception as e:
            print(f"Error fetching new members: {str(e)}")
            return 0

    def sync_members(self, db, Member) -> Dict:
        """Sync all members from BreezeChMS to local database"""
        try:
            # Get all people with their detailed profile information
            people = self.get_people()
            stats = {'created': 0, 'updated': 0, 'errors': 0}
            
            for person in people:
                try:
                    member = Member.query.filter_by(breeze_id=str(person.get('id', ''))).first()
                    
                    # Extract basic member data
                    member_data = {
                        'breeze_id': str(person.get('id', '')),
                        'first_name': str(person.get('first_name', '')),
                        'last_name': str(person.get('last_name', '')),
                        'email': str(person.get('email', '')),
                        'phone': str(person.get('phone', '')),
                        'status': str(person.get('status', '')),
                        'photo_url': str(person.get('photo_url', '')),
                        'created_at': datetime.strptime(person.get('created'), '%Y-%m-%d %H:%M:%S') if person.get('created') else None,
                        'updated_at': datetime.strptime(person.get('modified'), '%Y-%m-%d %H:%M:%S') if person.get('modified') else None
                    }
                    
                    # Extract additional profile fields if available
                    details = person.get('details', {})
                    if details:
                        member_data.update({
                            'address': str(details.get('address', '')),
                            'city': str(details.get('city', '')),
                            'state': str(details.get('state', '')),
                            'zip': str(details.get('zip', '')),
                            'membership_date': datetime.strptime(details.get('membership_date'), '%Y-%m-%d').date() if details.get('membership_date') else None,
                            'baptism_date': datetime.strptime(details.get('baptism_date'), '%Y-%m-%d').date() if details.get('baptism_date') else None
                        })
                    
                    if member:
                        # Update existing member
                        for key, value in member_data.items():
                            if hasattr(member, key):  # Only set if the attribute exists
                                setattr(member, key, value)
                        stats['updated'] += 1
                    else:
                        # Create new member
                        member = Member(**member_data)
                        db.session.add(member)
                        stats['created'] += 1
                    
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    stats['errors'] += 1
                    print(f"Error syncing member {person.get('id')}: {str(e)}")
            
            return stats
        except Exception as e:
            print(f"Error in sync_members: {str(e)}")
            return {'created': 0, 'updated': 0, 'errors': 1}