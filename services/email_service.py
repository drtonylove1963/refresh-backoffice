import logging
import time
from typing import Optional
from flask import render_template, render_template_string, current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
from models import EmailTemplate

def send_staff_notification(visitor) -> bool:
    """Send notification to staff about new visitor registration."""
    try:
        send_email(
            subject='New Visit Registration',
            to_email=current_app.config['STAFF_EMAIL'],
            template_name='staff_notification',
            template_data={'visitor': visitor, 'config': current_app.config}
        )
        return True
    except Exception as e:
        logging.error(f"Failed to send staff notification: {str(e)}")
        return False

def send_visitor_confirmation(visitor) -> bool:
    """Send confirmation email to visitor."""
    try:
        send_email(
            subject='Welcome to Refresh Church!',
            to_email=visitor.email,
            template_name='visitor_confirmation',
            template_data={'visitor': visitor, 'config': current_app.config}
        )
        return True
    except Exception as e:
        logging.error(f"Failed to send visitor confirmation: {str(e)}")
        return False

def send_email(subject: str, to_email: str, template_name: str, template_data: dict, max_retries: int = 3) -> bool:
    """Send an email using SendGrid with retry logic and improved error handling."""
    if not to_email or '@' not in to_email:
        logging.error(f"Invalid email address: {to_email}")
        raise ValueError("Invalid email address")

    if not current_app.config.get('SENDGRID_API_KEY'):
        logging.error("SendGrid API key is not configured")
        raise ValueError("SendGrid API key is not configured")

    try:
        # Get SendGrid client
        sg = SendGridAPIClient(api_key=current_app.config['SENDGRID_API_KEY'])
        
        # Try to get custom template from database
        custom_template = EmailTemplate.query.filter_by(template_type=template_name).first()
        
        if custom_template:
            # Use custom template
            html_content = render_template_string(custom_template.html_content, **template_data)
            email_subject = custom_template.subject
        else:
            # Fall back to default template
            html_content = render_template(f'email/{template_name}.html', **template_data)
            email_subject = subject
        
        message = Mail(
            from_email=Email(current_app.config.get('MAIL_DEFAULT_SENDER')),
            to_emails=To(to_email),
            subject=email_subject,
            html_content=HtmlContent(html_content)
        )

        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                response = sg.send(message)
                if response.status_code in [200, 201, 202]:
                    logging.info(f"Email sent successfully to {to_email}. Status code: {response.status_code}")
                    return True
                else:
                    raise Exception(f"SendGrid API returned status code: {response.status_code}")
            except Exception as e:
                last_error = e
                retry_count += 1
                logging.warning(f"Email sending attempt {retry_count} failed: {str(e)}")
                if retry_count < max_retries:
                    time.sleep(2 ** retry_count)  # Exponential backoff
        
        # If we've exhausted all retries, log and return False
        logging.error(f"Failed to send email after {max_retries} attempts. Last error: {str(last_error)}")
        return False
        
    except Exception as e:
        logging.error(f"Email preparation failed: {str(e)}")
        return False
