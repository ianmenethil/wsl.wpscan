# mailer.py
import sys
import os
import logging
import smtplib
from typing import Any, Optional
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import zipfile
import shutil
from rich.logging import RichHandler
import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    handlers=[
                        RichHandler(show_time=True,
                                    omit_repeated_times=False,
                                    show_level=True,
                                    show_path=True,
                                    enable_link_path=True,
                                    markup=True,
                                    rich_tracebacks=True,
                                    tracebacks_width=200,
                                    tracebacks_show_locals=False,
                                    tracebacks_theme='monokai',
                                    tracebacks_extra_lines=0,
                                    log_time_format='[%X]')
                    ])

ALLOWED_EXTENSIONS: set[str] = {'.xlsx', '.png', '.zip'}
CONFIGURATION_FILE: str = '_configs/config.yaml'

TODAYIS = datetime.now().strftime('%d-%m-%y')
DNSTWISTRESULTSFILE: str = f'Excel/DNSTwist/DNSTwistResults_{TODAYIS}.xlsx'
WPSCANRESULTSFILE: str = f'Excel/WPScanResults_{TODAYIS}.xlsx'
SCZIP = 'Excel/SmartCentral.zip'
PREZIP = 'Excel/PrePaid.zip'
ZPZIP = 'Excel/ZenPay.zip'
SCREENSHOTSBASEDIR: str = 'Excel/backup_' + TODAYIS
SCREENSHOTSBASEDIR_ZENPAY: str = SCREENSHOTSBASEDIR + '/ZenPay'
SCREENSHOTSBASEDIR_PREPAId: str = SCREENSHOTSBASEDIR + '/PrePaid'
SCREENSHOTSBASEDIR_SC: str = SCREENSHOTSBASEDIR + '/SmartCentral'


def read_config_file() -> Optional[dict[str, Any]]:
    try:
        with open(file=CONFIGURATION_FILE, mode='r', encoding='utf-8') as file:
            return yaml.safe_load(stream=file)
    except FileNotFoundError:
        logger.error("Config file not found: %s", CONFIGURATION_FILE)
    except yaml.YAMLError as exc:
        logger.error("Error in configuration file: %s", exc)
    return None


def send_email(config, output_files, scan_type) -> None:
    """Send email with attachment, customized based on scan type."""
    message = MIMEMultipart('alternative')
    message['From'] = f"Zen Alerts <{config['SENDER_EMAIL']}>"
    recipients = config['RECEIVER_EMAIL']
    if isinstance(recipients, str):  # For backward compatibility
        recipients = [recipients]
    message['To'] = ', '.join(recipients)

    # ! DNSTwist email customization
    if scan_type == 'DNSTwist':
        subject = f"DNSTwist Domain Security Alert - {TODAYIS}"
        body_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #007bff; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f2f2f2; color: black; padding: 10px; text-align: center; font-size: 0.8em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{scan_type} Domain Security Report</h1>
            </div>
            <div class="content">
                <p>This email contains important information regarding potential security risks identified in your domain names. The attached file(s) includes a detailed analysis of similar-looking domains that could be used for malicious purposes.</p>
                <p>It is crucial to review these findings to protect your domain's integrity and prevent potential phishing attacks.</p>
                <p>Please review the attached documents for details.</p>
            </div>
            <div class="footer">
                <p>This is an automated vulnerability alert. Please do not reply to this email.</p>
                <p style="color: purple; font-style: italic;">For any questions, please email <a href="mailto:ian@zenithpayments.com.au">ian@zenithpayments.com.au</a></p>
            </div>
        </body>
        </html>
        """
        body_text = f"DNSTwist Domain Security Alert - {TODAYIS}\nPlease review the attached security report for details."

    # WPScan email customization
    elif scan_type == 'WPScan':
        subject = f"WPScan Vulnerability Report - {TODAYIS}"
        body_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #dc3545; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f2f2f2; color: black; padding: 10px; text-align: center; font-size: 0.8em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{scan_type} Website Vulnerability Insights</h1>
            </div>
            <div class="content">
                <p>The attached file(s) contains an in-depth analysis of your WordPress site's vulnerabilities. This report highlights potential security risks that could compromise your website's integrity and the safety of its users.</p>
                <p>All vulnerabilities must be reviewed carefully to ensure the highest level of security.</p>
                <p>Please review the attached documents for details.</p>
            </div>
            <div class="footer">
                <p>This is an automated vulnerability alert. Please do not reply to this email.</p>
                <p style="color: purple; font-style: italic;">For any questions, please email <a href="mailto:ian@zenithpayments.com.au">ian@zenithpayments.com.au</a></p>
            </div>
        </body>
        </html>
        """
        body_text = f"WPScan Vulnerability Report - {TODAYIS}\nPlease review the attached document for detailed insights."
    message['Subject'] = subject

    # Attach text and HTML parts
    text_part = MIMEText(body_text, "plain")
    html_part = MIMEText(body_html, "html")
    message.attach(text_part)
    message.attach(html_part)

    for output_file in output_files:

        if not output_file:
            logger.info("No output file to attach.")
            continue
        extension = os.path.splitext(output_file)[1]
        if extension not in ALLOWED_EXTENSIONS:
            continue
        try:
            with open(file=output_file, mode='rb') as file:
                file_contents = file.read()
                attachment = MIMEApplication(file_contents, Name=os.path.basename(output_file))
                attachment['Content-Disposition'] = f'attachment; filename="{os.path.basename(output_file)}"'
                logger.info("Attaching file: %s", output_file)
                message.attach(attachment)
        except FileNotFoundError as file_not_found_err:
            logger.error("Failed to read and attach file: %s. Error: %s", output_file, str(file_not_found_err))
        except PermissionError as permission_err:
            logger.error("Failed to read and attach file: %s. Error: %s", output_file, str(permission_err))
        except ValueError as value_err:
            logger.error("Failed due to a value error. Error: %s", str(value_err))
        except Exception as err_exception:
            logger.error("Failed to read and attach file: %s. Error: %s", output_file, str(err_exception))
    try:
        with smtplib.SMTP(config['SMTPSERVER'], int(config['SMTPPORT']), local_hostname='localhost') as server:
            server.starttls()
            server.login(user=config['SENDER_EMAIL'], password=config['SENDER_PASSWORD'])
            server.sendmail(from_addr=config['SENDER_EMAIL'], to_addrs=recipients, msg=message.as_string())
    except smtplib.SMTPException as error:
        logger.error("An error occurred while sending the email: %s", error)
    else:
        logger.info("Email sent with attachments.")


def zipScreenshotsDIR(folder) -> str | None:
    """Zip screenshots folder"""
    zip_file_name = f'{folder}.zip'
    if os.path.exists(zip_file_name):
        return zip_file_name

    try:
        with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(folder):
                for file in files:
                    zip_file.write(os.path.join(root, file))
        return zip_file_name
    except Exception as e:
        logger.error(f"Error zipping screenshots folder: {e}")
        return None


def move_files(sourceFile, destinationFile) -> None:
    try:
        logger.info(f"Copying files {sourceFile} to {destinationFile}")
        shutil.copy(sourceFile, destinationFile)
    except Exception as e:
        logger.error(f"Error copying file: {e}")
        return None
    else:
        logger.info(f"File copied from {sourceFile} to {destinationFile}")


EXCELDIR = 'Excel'


def main() -> None:
    config = read_config_file()
    if config is None:
        logger.error("Error reading config file. Exiting.")
        return
    try:
        zip_filename = zipScreenshotsDIR(SCREENSHOTSBASEDIR_ZENPAY)
        if zip_filename is None:
            logger.error("Error creating zip file for screenshots. Exiting.")
            sys.exit()
        move_files(zip_filename, EXCELDIR)

        logger.info(f"ZenPay Email sent with screenshots {zip_filename}")
        zip_filename = zipScreenshotsDIR(SCREENSHOTSBASEDIR_PREPAId)
        if zip_filename is None:
            logger.error("Error creating zip file for screenshots. Exiting.")
            sys.exit()
        move_files(zip_filename, EXCELDIR)
        logger.info(f"PrePaid Email sent with screenshots {zip_filename}")
        zip_filename = zipScreenshotsDIR(SCREENSHOTSBASEDIR_SC)
        if zip_filename is None:
            logger.error("Error creating zip file for screenshots. Exiting.")
            sys.exit()
        move_files(zip_filename, EXCELDIR)
        logger.info(f"SmartCentral Email sent with screenshots {zip_filename}")
    except Exception as e:
        logger.error(f"Error creating zip file for screenshots: {e}")
        sys.exit()
    try:
        output_files = [DNSTWISTRESULTSFILE, ZPZIP, PREZIP, SCZIP]
        if output_files is None:
            logger.error("Error reading config file. Exiting.")
            sys.exit()
        send_email(config, output_files, "DNSTwist")  # For DNSTwist results
        logger.info(f"DNSTwist Email sent {output_files}")
        output_files = [WPSCANRESULTSFILE]
        if output_files is None:
            logger.error("Error reading config file. Exiting.")
            sys.exit()
        send_email(config, output_files, "WPScan")  # For WPScan results

        logger.info(f"WPScan Email sent {output_files}")
    except Exception as e:
        logger.error(f"Error creating zip file for screenshots: {e}")


if __name__ == "__main__":
    main()
