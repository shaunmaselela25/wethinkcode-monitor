import requests 
from bs4 import BeautifulSoup
import time
import json
import logging 
from datetime import datetime
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CONFIG_FILE = Path("config.json")
STATE_FILE = Path("wethinkcode_state.json")
LOG_FILE = Path("wethinkcode_monitor.log")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(LOG_FILE),
    logging.StreamHandler()
])

logger = logging.getLogger(__name__)

class WeThinkCodeMonitor:
    def __init__(self, config_path=CONFIG_FILE):
        self.config = self.load_config(config_path)
        self.state = self.load_state()
        self.url = self.config.get('url', 'https://www.apply.wethinkcode.co.za/requirements') 

    def load_config(self, config_path):
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            default_config = {
                "url": "https://www.apply.wethinkcode.co.za/requirements",
                "check_interval_hours": 6,
                "alert_methods" : {
                    "email": False,
                    "console": True,
                    "file": True
                },
                "email_config": {
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "sender_email": "your_email_address",
                    "sender_password": "your_email_password",
                    "recipient_email": "your_email_address"
                },

                "keywords": [
                    "apply",
                    "application",
                    "open",
                    "register",
                    "registration"
                ]
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
                logger.info(f"Default config created at {config_path}")
                return default_config
            
    def load_state(self):
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        else:
            return {"application_open": False, "last_status": None, "last_status_change": None}
        
    def save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=4)

    def check_application_status(self):
        try:
            logger.info(f"Checking application status at {self.url}")

            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get(self.url)
                time.sleep(5)
                
                page_text = driver.page_source.lower()
                body_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
                
                logger.debug(f"Page text snippet: {body_text[:500]}")
                
            finally:
                driver.quit()

            application_open = False
            found_keywords = []

            if any(phrase in body_text for phrase in [
                "officially closed", 
                "applications are closed",
                "applications closed",
                "not accepting",
                "no longer accepting"
            ]):
                application_open = False
                found_keywords.append("closed")
            elif "0 days" in body_text and "0 hrs" in body_text:
                application_open = False
                found_keywords.append("countdown expired")
            elif any(phrase in body_text for phrase in [
                "apply now",
                "register now", 
                "applications open",
                "applications are open",
                "now open"
            ]):
                application_open = True
                found_keywords.append("open")
            else:
                keywords = self.config.get('keywords', [])
                for keyword in keywords:
                    if keyword.lower() in body_text:
                        found_keywords.append(keyword)
                
                if len(found_keywords) >= 2:
                    application_open = True

            status_message = f"Application Status: {'OPEN' if application_open else 'CLOSED'}"
            if found_keywords:
                status_message += f" (Found: {', '.join(found_keywords)})"

            logger.info(status_message)
            return application_open, status_message
    
        except Exception as e:
            logger.error(f"Error checking application status: {e}")
            return None, f"Error checking application status: {e}"
    
    def send_email_alert(self, subject, message):
        if not self.config['alert_methods'].get('email', False):
            return  
         
        try:
            email_config = self.config['email_config']
            sender_email = email_config['sender_email']
            recipient_email = email_config['recipient_email']

            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
           
            body = f"""
WeThinkCode Application Status Alert

{message}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
URL: {self.url}
"""
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(sender_email, email_config['sender_password'])
                server.send_message(msg)
            
            logger.info(f"Email alert sent to {recipient_email}")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    def send_file_alert(self, message):
        if not self.config['alert_methods'].get('file', False):
            return
        
        alert_file = Path("alerts.txt")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(alert_file, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
        
        logger.info(f"Alert written to {alert_file}")
    
    def send_console_alert(self, message):
        if not self.config['alert_methods'].get('console', True):
            return
        
        separator = "=" * 60
        print(f"\n{separator}")
        print(f"🚨 ALERT: WeThinkCode Application Status")
        print(separator)
        print(f"Message: {message}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"URL: {self.url}")
        print(f"{separator}\n")
    
    def send_alerts(self, message):
        subject = "🚨 WeThinkCode Applications ARE OPEN!"
        
        self.send_console_alert(message)
        self.send_file_alert(message)
        self.send_email_alert(subject, message)
    
    def run_check(self):
        is_open, status_message = self.check_application_status()
        
        if is_open is None:
            logger.warning("Could not determine application status")
            return
        
        current_time = datetime.now().isoformat()
        previous_status = self.state.get('application_open', False)
        
        self.state['last_checked'] = current_time
        
        if is_open != previous_status:
            self.state['application_open'] = is_open
            self.state['last_status_change'] = current_time
            
            if is_open:
                alert_message = f"✅ WeThinkCode applications are NOW OPEN! Visit {self.url} to apply!"
                logger.info("STATUS CHANGE: Applications opened!")
                self.send_alerts(alert_message)
            else:
                logger.info("STATUS CHANGE: Applications closed")
                self.send_console_alert(f"Applications are now closed. {status_message}")
        else:
            logger.info(f"No status change. Current status: {status_message}")
        
        self.save_state()
    
    def run_continuous(self):
        check_interval_hours = self.config.get('check_interval_hours', 24)
        check_interval_seconds = check_interval_hours * 3600
        
        logger.info(f"Starting continuous monitoring (checking every {check_interval_hours} hours)")
        
        while True:
            try:
                self.run_check()
                logger.info(f"Next check in {check_interval_hours} hours")
                time.sleep(check_interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(300)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Monitor WeThinkCode application status and send alerts'
    )
    parser.add_argument(
        '--mode',
        choices=['once', 'continuous'],
        default='continuous',
        help='Run mode: once (single check) or continuous (scheduled checks)'
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    monitor = WeThinkCodeMonitor(config_path=Path(args.config))
    
    if args.mode == 'once':
        logger.info("Running single check...")
        monitor.run_check()
    else:
        logger.info("Starting continuous monitoring...")
        monitor.run_continuous()


if __name__ == "__main__":
    main()
