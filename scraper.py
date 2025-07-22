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

class BookMyShowScraper:
    def __init__(self):
        self.base_url = "https://in.bookmyshow.com/explore/events-mumbai?categories=music-shows"
        self.events_file = "previous_events.json"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def scrape_events(self):
        """Scrape events from BookMyShow"""
        try:
            print("🔍 Fetching BookMyShow page...")
            
            # Add random delay to appear more human
            time.sleep(random.uniform(2, 5))
            
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            
            # Multiple selectors to catch different layouts
            event_selectors = [
                'div[data-testid="event-card"]',
                '.event-card',
                '.event-item',
                '[class*="event"]',
                'article',
                '.list-card'
            ]
            
            event_elements = []
            for selector in event_selectors:
                elements = soup.select(selector)
                if elements:
                    event_elements = elements
                    print(f"✅ Found events using selector: {selector}")
                    break
            
            if not event_elements:
                # Fallback: look for any links containing 'events'
                event_elements = soup.find_all('a', href=lambda x: x and 'events' in x)
                print(f"🔄 Fallback: Found {len(event_elements)} event links")
            
            for element in event_elements[:20]:  # Limit to first 20 events
                try:
                    event = self.extract_event_data(element)
                    if event and event['title']:
                        events.append(event)
                except Exception as e:
                    print(f"⚠️ Error extracting event: {e}")
                    continue
            
            print(f"📊 Total events found: {len(events)}")
            return events
            
        except requests.RequestException as e:
            print(f"❌ Error fetching page: {e}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return []
    
    def extract_event_data(self, element):
        """Extract event details from HTML element"""
        event = {
            'title': '',
            'date': '',
            'venue': '',
            'price': '',
            'url': ''
        }
        
        # Title extraction (multiple approaches)
        title_selectors = [
            'h1, h2, h3, h4',
            '[data-testid*="title"]',
            '.title',
            '.event-title',
            '.name'
        ]
        
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem and title_elem.get_text(strip=True):
                event['title'] = title_elem.get_text(strip=True)
                break
        
        # If no title found, try the element text itself
        if not event['title']:
            text = element.get_text(strip=True)
            if text and len(text) < 200:
                event['title'] = text[:100]
        
        # Date extraction
        date_selectors = [
            '[data-testid*="date"]',
            '.date',
            '.event-date',
            '[class*="date"]'
        ]
        
        for selector in date_selectors:
            date_elem = element.select_one(selector)
            if date_elem:
                event['date'] = date_elem.get_text(strip=True)
                break
        
        # Venue extraction
        venue_selectors = [
            '[data-testid*="venue"]',
            '.venue',
            '.location',
            '[class*="venue"]',
            '[class*="location"]'
        ]
        
        for selector in venue_selectors:
            venue_elem = element.select_one(selector)
            if venue_elem:
                event['venue'] = venue_elem.get_text(strip=True)
                break
        
        # Price extraction
        price_selectors = [
            '[data-testid*="price"]',
            '.price',
            '[class*="price"]',
            '[class*="cost"]'
        ]
        
        for selector in price_selectors:
            price_elem = element.select_one(selector)
            if price_elem:
                event['price'] = price_elem.get_text(strip=True)
                break
        
        # URL extraction
        link = element.find('a')
        if link and link.get('href'):
            url = link.get('href')
            if url.startswith('/'):
                event['url'] = f"https://in.bookmyshow.com{url}"
            elif url.startswith('http'):
                event['url'] = url
        
        # Create unique ID for event
        event['id'] = f"{event['title'][:50]}_{event['date'][:20]}".replace(' ', '_').lower()
        
        return event
    
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
    
    def send_email_alert(self, new_events):
        """Send email with new events"""
        try:
            sender_email = os.environ.get('SENDER_EMAIL')
            sender_password = os.environ.get('SENDER_PASSWORD')
            receiver_email = os.environ.get('RECEIVER_EMAIL')
            smtp_server = os.environ.get('SMTP_SERVER')
            
            if not all([sender_email, sender_password, receiver_email]):
                print("❌ Missing email credentials")
                return False
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🎵 {len(new_events)} New Music Events in Mumbai!"
            msg['From'] = sender_email
            msg['To'] = receiver_email
            
            # Create HTML email body
            html_body = self.create_email_html(new_events)
            
            # Create text version
            text_body = self.create_email_text(new_events)
            
            # Attach both versions
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
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
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px; margin-bottom: 20px; }
                .event-card { border: 1px solid #ddd; margin: 15px 0; padding: 20px; border-radius: 10px; background: #f9f9f9; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                .event-title { font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }
                .event-detail { margin: 8px 0; padding: 5px 0; border-bottom: 1px solid #eee; }
                .event-detail:last-child { border-bottom: none; }
                .label { font-weight: bold; color: #34495e; }
                .book-btn { background: #e74c3c; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 15px; }
                .footer { margin-top: 30px; padding: 20px; background: #ecf0f1; border-radius: 10px; text-align: center; font-size: 14px; color: #7f8c8d; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎵 New Music Events in Mumbai!</h1>
                <p>Found """ + str(len(events)) + """ new events on BookMyShow</p>
            </div>
        """
        
        for event in events:
            html += f"""
            <div class="event-card">
                <div class="event-title">{event['title']}</div>
                <div class="event-detail"><span class="label">📅 Date:</span> {event['date'] or 'Not specified'}</div>
                <div class="event-detail"><span class="label">📍 Venue:</span> {event['venue'] or 'Not specified'}</div>
                <div class="event-detail"><span class="label">💰 Price:</span> {event['price'] or 'Check website'}</div>
                {f'<a href="{event["url"]}" class="book-btn">Book Now →</a>' if event['url'] else ''}
            </div>
            """
        
        html += f"""
            <div class="footer">
                <p>This alert was generated automatically on {datetime.now().strftime('%Y-%m-%d at %H:%M IST')}</p>
                <p>🔗 <a href="https://in.bookmyshow.com/explore/events-mumbai?categories=music-shows">View all Mumbai music events</a></p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def create_email_text(self, events):
        """Create plain text email body"""
        text = f"🎵 NEW MUSIC EVENTS IN MUMBAI! 🎵\n\n"
        text += f"Found {len(events)} new events:\n"
        text += "=" * 50 + "\n\n"
        
        for i, event in enumerate(events, 1):
            text += f"{i}. {event['title']}\n"
            if event['date']:
                text += f"   📅 Date: {event['date']}\n"
            if event['venue']:
                text += f"   📍 Venue: {event['venue']}\n"
            if event['price']:
                text += f"   💰 Price: {event['price']}\n"
            if event['url']:
                text += f"   🔗 Link: {event['url']}\n"
            text += "\n" + "-" * 30 + "\n\n"
        
        text += f"Generated on: {datetime.now().strftime('%Y-%m-%d at %H:%M IST')}\n"
        text += "View all events: https://in.bookmyshow.com/explore/events-mumbai?categories=music-shows"
        
        return text
    
    def run(self):
        """Main execution function"""
        print("🚀 Starting BookMyShow scraper...")
        print(f"⏰ Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
        
        # Load previous events
        previous_events = self.load_previous_events()
        print(f"📚 Loaded {len(previous_events)} previous events")
        
        # Scrape current events
        current_events = self.scrape_events()
        
        if not current_events:
            print("❌ No events found - possibly blocked or page changed")
            return
        
        # Find new events
        new_events = self.find_new_events(current_events, previous_events)
        
        # Save current events
        self.save_events(current_events)
        
        # Send email if new events found
        if new_events:
            print(f"📧 Sending email alert for {len(new_events)} new events...")
            self.send_email_alert(new_events)
        else:
            print("✅ No new events found - no email sent")
        
        print("🏁 Scraper completed successfully!")

if __name__ == "__main__":
    scraper = BookMyShowScraper()
    scraper.run()
