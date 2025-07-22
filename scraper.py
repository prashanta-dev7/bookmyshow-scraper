import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from datetime import datetime
import time
import random
import urllib.parse

class BookMyShowScraper:
    def __init__(self):
        self.events_file = "previous_events.json"
        
        # Multiple approaches to access BookMyShow data
        self.methods = [
            self.method_1_google_cache,
            self.method_2_web_archive,
            self.method_3_mobile_version,
            self.method_4_api_endpoint
        ]
        
        # Different user agents to rotate
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/111.0 Firefox/111.0'
        ]
    
    def get_headers(self):
        """Get randomized headers"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    
    def method_1_google_cache(self):
        """Try Google's cached version of BookMyShow"""
        print("🔍 Method 1: Trying Google Cache...")
        
        try:
            # Google cache URL
            original_url = "https://in.bookmyshow.com/explore/events-mumbai?categories=music-shows"
            cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{urllib.parse.quote(original_url)}"
            
            headers = self.get_headers()
            response = requests.get(cache_url, headers=headers, timeout=30)
            
            if response.status_code == 200 and 'bookmyshow' in response.text.lower():
                print("✅ Google cache worked!")
                return self.extract_events_from_html(response.text, "Google Cache")
            else:
                print("❌ Google cache failed")
                return []
                
        except Exception as e:
            print(f"❌ Google cache error: {e}")
            return []
    
    def method_2_web_archive(self):
        """Try Archive.today/Web Archive versions"""
        print("🔍 Method 2: Trying Web Archive...")
        
        try:
            # Try archive.today
            archive_urls = [
                "https://archive.today/newest/https://in.bookmyshow.com/explore/events-mumbai?categories=music-shows",
                "https://web.archive.org/web/2/https://in.bookmyshow.com/explore/events-mumbai?categories=music-shows"
            ]
            
            for archive_url in archive_urls:
                try:
                    headers = self.get_headers()
                    response = requests.get(archive_url, headers=headers, timeout=30)
                    
                    if response.status_code == 200 and 'music' in response.text.lower():
                        print(f"✅ Archive version worked!")
                        return self.extract_events_from_html(response.text, "Web Archive")
                
                except Exception as e:
                    print(f"Archive URL failed: {e}")
                    continue
            
            print("❌ Web archive failed")
            return []
            
        except Exception as e:
            print(f"❌ Web archive error: {e}")
            return []
    
    def method_3_mobile_version(self):
        """Try mobile version of BookMyShow"""
        print("🔍 Method 3: Trying Mobile Version...")
        
        try:
            # Mobile URLs sometimes have different blocking rules
            mobile_urls = [
                "https://m.bookmyshow.com/explore/events-mumbai?categories=music-shows",
                "https://in.bookmyshow.com/mobile/events-mumbai?categories=music-shows"
            ]
            
            mobile_headers = self.get_headers()
            mobile_headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
            
            for mobile_url in mobile_urls:
                try:
                    time.sleep(random.uniform(3, 8))  # Random delay
                    response = requests.get(mobile_url, headers=mobile_headers, timeout=30)
                    
                    if response.status_code == 200:
                        print("✅ Mobile version worked!")
                        return self.extract_events_from_html(response.text, "Mobile BookMyShow")
                
                except Exception as e:
                    print(f"Mobile URL failed: {e}")
                    continue
            
            print("❌ Mobile version failed")
            return []
            
        except Exception as e:
            print(f"❌ Mobile version error: {e}")
            return []
    
    def method_4_api_endpoint(self):
        """Try to find API endpoints that BookMyShow might use"""
        print("🔍 Method 4: Trying API Endpoints...")
        
        try:
            # Sometimes there are public API endpoints
            api_urls = [
                "https://in.bookmyshow.com/api/explore/events?city=mumbai&category=music-shows",
                "https://in.bookmyshow.com/serv/getData?cmd=GETEVENTS&t=20250722&city=MUMBAI",
                "https://in.bookmyshow.com/bms/events?city=mumbai&type=music"
            ]
            
            api_headers = self.get_headers()
            api_headers.update({
                'Accept': 'application/json, text/plain, */*',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://in.bookmyshow.com/'
            })
            
            for api_url in api_urls:
                try:
                    time.sleep(random.uniform(2, 5))
                    response = requests.get(api_url, headers=api_headers, timeout=30)
                    
                    if response.status_code == 200:
                        try:
                            # Try JSON response
                            data = response.json()
                            print("✅ API endpoint worked!")
                            return self.extract_events_from_json(data, "BookMyShow API")
                        except:
                            # Try HTML response
                            if 'music' in response.text.lower():
                                print("✅ API endpoint (HTML) worked!")
                                return self.extract_events_from_html(response.text, "BookMyShow API")
                
                except Exception as e:
                    print(f"API URL failed: {e}")
                    continue
            
            print("❌ API endpoints failed")
            return []
            
        except Exception as e:
            print(f"❌ API endpoints error: {e}")
            return []
    
    def extract_events_from_html(self, html_content, source):
        """Extract events from HTML content"""
        events = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Multiple selectors to try for BookMyShow events
            selectors = [
                '[data-testid*="event"]',
                '.event-card', '.eventCard',
                '.event-item', '.eventItem',
                '.listing-card', '.listingCard',
                'div[class*="event"]',
                'article[class*="event"]',
                '.card[href*="/events/"]',
                'a[href*="/events/"]'
            ]
            
            event_elements = []
            for selector in selectors:
                elements = soup.select(selector)
                if elements and len(elements) > 2:  # Need at least 3 events
                    event_elements = elements
                    print(f"✅ Found {len(elements)} events using selector: {selector}")
                    break
            
            # If no specific selectors work, try to find event-like content
            if not event_elements:
                # Look for links containing 'events'
                event_elements = soup.find_all('a', href=lambda x: x and 'events' in x)[:20]
                if event_elements:
                    print(f"✅ Found {len(event_elements)} event links as fallback")
            
            for element in event_elements[:15]:  # Limit to 15 events
                try:
                    event = self.extract_single_event(element, soup)
                    if event and event.get('title'):
                        event['source'] = source
                        events.append(event)
                except Exception as e:
                    continue
            
            # Additional text-based extraction for cached pages
            if not events:
                events = self.extract_events_from_text(html_content, source)
            
            print(f"📊 Extracted {len(events)} events from {source}")
            return events
            
        except Exception as e:
            print(f"❌ HTML extraction error: {e}")
            return []
    
    def extract_single_event(self, element, soup):
        """Extract single event details"""
        event = {
            'title': '',
            'date': '',
            'venue': '',
            'price': '',
            'url': '',
            'id': ''
        }
        
        try:
            # Title extraction
            title_selectors = ['h1', 'h2', 'h3', 'h4', '[data-testid*="title"]', '.title', '.name']
            for selector in title_selectors:
                title_elem = element.find(selector) if hasattr(element, 'find') else element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 5:
                        event['title'] = title
                        break
            
            # If no title found, use element text or href
            if not event['title']:
                if hasattr(element, 'get_text'):
                    text = element.get_text(strip=True)
                    if text and len(text) < 150:
                        event['title'] = text
                elif hasattr(element, 'get') and element.get('href'):
                    # Extract title from URL
                    href = element.get('href', '')
                    if '/events/' in href:
                        title_from_url = href.split('/events/')[-1].replace('-', ' ').replace('/', '').title()
                        event['title'] = title_from_url[:100]
            
            # Date extraction
            date_selectors = [
                '[data-testid*="date"]', '.date', '.event-date',
                'time', '.datetime', '[class*="date"]'
            ]
            for selector in date_selectors:
                date_elem = element.find(selector) if hasattr(element, 'find') else element.select_one(selector)
                if date_elem:
                    event['date'] = date_elem.get_text(strip=True)
                    break
            
            # Venue extraction
            venue_selectors = [
                '[data-testid*="venue"]', '.venue', '.location',
                '[class*="venue"]', '[class*="location"]'
            ]
            for selector in venue_selectors:
                venue_elem = element.find(selector) if hasattr(element, 'find') else element.select_one(selector)
                if venue_elem:
                    event['venue'] = venue_elem.get_text(strip=True)
                    break
            
            if not event['venue']:
                event['venue'] = 'Mumbai'
            
            # Price extraction
            price_selectors = [
                '[data-testid*="price"]', '.price', '[class*="price"]',
                '[class*="cost"]', '.amount'
            ]
            for selector in price_selectors:
                price_elem = element.find(selector) if hasattr(element, 'find') else element.select_one(selector)
                if price_elem:
                    event['price'] = price_elem.get_text(strip=True)
                    break
            
            if not event['price']:
                event['price'] = 'Check website'
            
            # URL extraction
            if hasattr(element, 'get') and element.get('href'):
                href = element.get('href')
                if href.startswith('/'):
                    event['url'] = f"https://in.bookmyshow.com{href}"
                elif href.startswith('http'):
                    event['url'] = href
            elif hasattr(element, 'find'):
                link_elem = element.find('a')
                if link_elem and link_elem.get('href'):
                    href = link_elem.get('href')
                    if href.startswith('/'):
                        event['url'] = f"https://in.bookmyshow.com{href}"
                    elif href.startswith('http'):
                        event['url'] = href
            
            # Create unique ID
            title_for_id = event['title'][:50] if event['title'] else 'event'
            date_for_id = event['date'][:20] if event['date'] else datetime.now().strftime('%Y%m%d')
            event['id'] = f"{title_for_id}_{date_for_id}".replace(' ', '_').lower()
            
            # Only return events that seem to be music-related
            title_lower = event['title'].lower()
            if any(keyword in title_lower for keyword in ['music', 'concert', 'live', 'show', 'performance', 'gig', 'festival']):
                return event
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error extracting single event: {e}")
            return None
    
    def extract_events_from_json(self, json_data, source):
        """Extract events from JSON API response"""
        events = []
        
        try:
            # Handle different JSON structures
            if isinstance(json_data, dict):
                # Try common JSON structures
                events_data = json_data.get('events', json_data.get('data', json_data.get('results', [])))
            elif isinstance(json_data, list):
                events_data = json_data
            else:
                return []
            
            for item in events_data[:15]:
                try:
                    event = {
                        'title': item.get('name', item.get('title', item.get('eventName', ''))),
                        'date': item.get('date', item.get('eventDate', item.get('startDate', ''))),
                        'venue': item.get('venue', item.get('location', 'Mumbai')),
                        'price': item.get('price', item.get('ticketPrice', 'Check website')),
                        'url': item.get('url', item.get('bookingUrl', '')),
                        'source': source
                    }
                    
                    if event['title']:
                        event['id'] = f"{event['title'][:50]}_{event['date'][:20]}".replace(' ', '_').lower()
                        events.append(event)
                        
                except Exception as e:
                    continue
            
            return events
            
        except Exception as e:
            print(f"❌ JSON extraction error: {e}")
            return []
    
    def extract_events_from_text(self, text_content, source):
        """Extract events from plain text (fallback method)"""
        events = []
        
        try:
            # Look for patterns in text that might be events
            lines = text_content.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines or very short lines
                if len(line) < 10 or len(line) > 200:
                    continue
                
                # Look for music-related keywords
                if any(keyword in line.lower() for keyword in ['concert', 'music', 'live', 'show', 'festival', 'performance']):
                    # Skip navigation/menu items
                    if any(skip in line.lower() for skip in ['menu', 'login', 'sign up', 'footer', 'header', 'search']):
                        continue
                    
                    event = {
                        'title': line,
                        'date': 'Check website',
                        'venue': 'Mumbai',
                        'price': 'Check website',
                        'url': 'https://in.bookmyshow.com/explore/events-mumbai?categories=music-shows',
                        'source': source,
                        'id': f"{line[:50]}_{datetime.now().strftime('%Y%m%d')}".replace(' ', '_').lower()
                    }
                    
                    events.append(event)
                    
                    if len(events) >= 10:  # Limit to 10 events from text
                        break
            
            return events
            
        except Exception as e:
            print(f"❌ Text extraction error: {e}")
            return []
    
    def scrape_events(self):
        """Main scraping function that tries all methods"""
        all_events = []
        
        print("🚀 Starting BookMyShow scraping with multiple bypass methods...")
        
        for i, method in enumerate(self.methods, 1):
            print(f"\n🔄 Trying method {i}/4...")
            
            try:
                events = method()
                
                if events:
                    print(f"✅ Method {i} found {len(events)} events!")
                    all_events.extend(events)
                    break  # Stop at first successful method
                else:
                    print(f"❌ Method {i} found no events")
                
                # Add delay between methods
                time.sleep(random.uniform(5, 10))
                
            except Exception as e:
                print(f"❌ Method {i} failed: {e}")
                continue
        
        # Remove duplicates
        unique_events = []
        seen_titles = set()
        
        for event in all_events:
            title_key = event['title'].lower().strip()[:30]
            if title_key not in seen_titles and len(title_key) > 5:
                seen_titles.add(title_key)
                unique_events.append(event)
        
        print(f"\n📊 Final result: {len(unique_events)} unique events found")
        return unique_events[:20]  # Limit to 20 events
    
    def load_previous_events(self):
        """Load previously found events"""
        try:
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"⚠️ Error loading previous events: {e}")
            return []
    
    def save_events(self, events):
        """Save events to file"""
        try:
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved {len(events)} events to file")
        except Exception as e:
            print(f"❌ Error saving events: {e}")
    
    def find_new_events(self, current_events, previous_events):
        """Find new events by comparing current vs previous"""
        previous_ids = {event['id'] for event in previous_events}
        new_events = [event for event in current_events if event['id'] not in previous_ids]
        
        print(f"🆕 Found {len(new_events)} new events")
        return new_events
    
    def send_email_alert(self, events):
        """Send email with events"""
        try:
            sender_email = os.environ.get('SENDER_EMAIL')
            sender_password = os.environ.get('SENDER_PASSWORD')
            receiver_email = os.environ.get('RECEIVER_EMAIL')
            smtp_server = os.environ.get('SMTP_SERVER')
            
            if not all([sender_email, sender_password, receiver_email]):
                print("❌ Missing email credentials")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🎵 BookMyShow Mumbai Music Events - {len(events)} Found!"
            msg['From'] = sender_email
            msg['To'] = receiver_email
            
            # Create email body
            html_body = self.create_email_html(events)
            text_body = self.create_email_text(events)
            
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            with smtplib.SMTP(smtp_server, 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            print("✅ Email sent successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    def create_email_html(self, events):
        """Create HTML email body"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; padding: 20px; text-align: center; border-radius: 10px; margin-bottom: 20px; }}
                .event-card {{ border: 1px solid #ddd; margin: 15px 0; padding: 20px; border-radius: 10px; background: #f9f9f9; }}
                .event-title {{ font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
                .event-detail {{ margin: 8px 0; }}
                .source-tag {{ background: #3498db; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }}
                .book-btn {{ background: #e74c3c; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎵 BookMyShow Mumbai Music Events!</h1>
                <p>Found {len(events)} events</p>
            </div>
        """
        
        for event in events:
            html += f"""
            <div class="event-card">
                <div class="event-title">{event['title']} <span class="source-tag">{event['source']}</span></div>
                <div class="event-detail">📅 <strong>Date:</strong> {event['date']}</div>
                <div class="event-detail">📍 <strong>Venue:</strong> {event['venue']}</div>
                <div class="event-detail">💰 <strong>Price:</strong> {event['price']}</div>
                {f'<a href="{event["url"]}" class="book-btn">View Details →</a>' if event['url'] else ''}
            </div>
            """
        
        html += f"""
            <div style="margin-top: 30px; padding: 20px; background: #ecf0f1; border-radius: 10px; text-align: center;">
                <p>Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M IST')}</p>
                <p><a href="https://in.bookmyshow.com/explore/events-mumbai?categories=music-shows">Visit BookMyShow directly</a></p>
            </div>
        </body>
        </html>
        """
        return html
    
    def create_email_text(self, events):
        """Create plain text email"""
        text = f"🎵 BOOKMYSHOW MUMBAI MUSIC EVENTS!\n\nFound {len(events)} events:\n" + "="*50 + "\n\n"
        
        for i, event in enumerate(events, 1):
            text += f"{i}. {event['title']} [{event['source']}]\n"
            text += f"   📅 {event['date']}\n"
            text += f"   📍 {event['venue']}\n"
            text += f"   💰 {event['price']}\n"
            if event['url']:
                text += f"   🔗 {event['url']}\n"
            text += "\n" + "-"*30 + "\n\n"
        
        text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}"
        return text
    
    def run(self):
        """Main execution function"""
        print("🚀 Starting BookMyShow Mumbai Music Events Monitor...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
        
        # Load previous events
        previous_events = self.load_previous_events()
        print(f"📚 Loaded {len(previous_events)} previous events")
        
        # Scrape current events
        current_events = self.scrape_events()
        
        if not current_events:
            print("❌ No events found with any method")
            return
        
        # For testing, send all events (later you can switch to new events only)
        print(f"📧 Sending email with {len(current_events)} events...")
        self.send_email_alert(current_events)
        
        # Save current events
        self.save_events(current_events)
        
        print("🏁 Scraper completed successfully!")

if __name__ == "__main__":
    scraper = BookMyShowScraper()
    scraper.run()
