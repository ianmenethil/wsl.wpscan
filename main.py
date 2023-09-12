import logging
import os
import glob
import csv
import time
from datetime import timedelta, datetime
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import subprocess
import json
import yaml

INPUT_FILE_EXTENSION = '.json'
OUTPUT_DIRECTORY = './data'
TODAY = datetime.now().strftime("%d-%m-%Y")
ARCHIVE_DIR = os.path.join(OUTPUT_DIRECTORY, TODAY)
ALLOWED_EXTENSIONS = {'.csv'}
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
CONFIGURATION_FILE = 'config.yaml'
ERROR_STRINGS = ['The API token provided is invalid', 'Your API limit has been reached']
SCAN_START_TIME: datetime = datetime.now()

logging.basicConfig(
    level=logging.DEBUG,
    encoding="utf-8",
    format="%(asctime)s|%(levelname)s|%(message)s",
    datefmt=DATE_FORMAT,
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/wpscan.log", 'a', 'utf-8')]
    )
logging.getLogger("").setLevel(logging.INFO)

def read_config_file():  # Read config.yaml file.
    """ Returns: dict: Configuration data if successful, None otherwise."""
    try:
        with open(file=CONFIGURATION_FILE, mode='r', encoding='utf-8') as file:
            return yaml.safe_load(stream=file)
    except FileNotFoundError:
        logging.error("Config file not found: %s", CONFIGURATION_FILE)
        return None
    except yaml.YAMLError:
        logging.error("Error in configuration file:")
        return None

def format_timedelta(fmt_timedelta: timedelta):  # Format timedelta for human readability
    """ Args: fmt_timedelta (timedelta): The timedelta object to format. Returns: str: The formatted string. """
    minutes: int
    seconds: int
    minutes, seconds = divmod(fmt_timedelta.seconds, 60)
    # Now, convert them into integers
    hours: int
    hours, minutes = divmod(minutes, 60)
    return f"{hours} hours, {minutes} minutes, {seconds} seconds"

def get_domains_to_scan(config):  # Get list of domains to scan.
    """ Args: config (dict): The configuration dictionary.  Returns: list: A list of domain names to scan. """
    default_domains = config['DOMAIN_LIST']
    logging.info('Default domains:\n%s', '\n'.join(default_domains))
    domains = input("Enter domain names separated by commas (or leave blank to use domains from config): ").strip()
    domains_to_scan = domains.split(",") if domains else default_domains
    logging.info('Domains:\n%s', '\n'.join(domains_to_scan))
    return domains_to_scan

def get_email_recipients(config):  # Get email recipients
    """ Args: config (dict): The configuration dictionary. Returns: list: A list of email addresses of recipients. """
    logging.info("Default recipient email '%s'", config['DEFAULT_RECIPIENT_EMAIL_LIST'])
    if recipients := input("Enter recipient email addresses separated by commas (or leave blank to use emails from config): ").strip():
        recipients_list = recipients.split(",")
    else:
        recipients_list = config['DEFAULT_RECIPIENT_EMAIL_LIST'] if isinstance(config['DEFAULT_RECIPIENT_EMAIL_LIST'], list) else [config['DEFAULT_RECIPIENT_EMAIL_LIST']]
    logging.info("Recipients: %s", recipients_list)
    return recipients_list

def user_email_option():  # Get user email preference
    """ Returns: bool: True if the user chooses to email the output, False otherwise. """
    logging.info("Default email option is set as 'Do not send'")
    option: str = input("""Do you want to email the output?
1) No(default) | 2) Yes: """).strip()
    if not option:
        option = "1"
    logging.info("User chose option %s", option)
    return option == '2'

def run_wpscan(domain, api_key, key_index):  # Run wpscan subprocess
    """ Args:
        domain (str): The domain to scan.
        api_key (str): The API key for WPScan.
        key_index (int): The index of the API key in the list.
    Returns:
        list: A list of filenames of the WPScan output files.
        str: The output JSON or error message.
        bool: True if there was an API key error, False otherwise.
    """
    date_string = datetime.now().strftime("%Y-%m-%d")
    wpscan_file_extension: str = "json"
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(name=OUTPUT_DIRECTORY)
    version = 1
    filenames = []
    wpscan_output_file = os.path.join(OUTPUT_DIRECTORY, f"{domain}_{date_string}_WPScan_v{version}.{wpscan_file_extension}")
    while os.path.isfile(wpscan_output_file):
        version += 1
        wpscan_output_file = os.path.join(OUTPUT_DIRECTORY, f"{domain}_{date_string}_WPScan_v{version}.{wpscan_file_extension}")
        # filenames.append(wpscan_output_file)
    filenames.append(wpscan_output_file)
    logging.info('Using API key #%d for domain: %s', key_index + 1, domain)
    command = ['wpscan',
                '--url', domain,
                # '--verbose',
                '--no-banner',
                '--random-user-agent',
                '--update',
                '--detection-mode', 'mixed',
                # '--scope', '*.' + domain,
                '--random-user-agent',
                '--max-threads', '8',
                '--throttle', '500',
                '--clear-cache',
                '--interesting-findings-detection', 'mixed',
                '--force',
                '--wp-version-all',
                '--plugins-version-all',
                '--themes-version-all',
                '--plugins-threshold', '0',
                '--enumerate', 'vp,vt,tt,cb,dbe,u,m',
                '--headers', '"X-Forwarded-For:127.0.0.1; Another: Menethil"',
                '--cookie-jar', './cookies/' + domain + '_cookies.txt',
                '--cache-dir', './cache/',
                '--api-token', api_key,
                '--format', 'json',
                '--output', wpscan_output_file]

    if domain == 'travelpayb2b.com.au':
        command.extend(['--wp-content-dir', '/wp-content/'])
    try:
        filename, output_json_or_error, api_key_error = run_wpscan_subprocess(command, domain, wpscan_output_file)
        return [filename], output_json_or_error, api_key_error
    except subprocess.CalledProcessError as e_process_err:
        logging.error("An unexpected error occurred while scanning domain '%s': %s", domain, str(e_process_err))
        return filenames, str(e_process_err), True

def run_wpscan_subprocess(command, domain, wpscan_output_file):  # Helper to run wpscan subprocess
    """ Args:   command
                domain (str): The domain to scan.
                wpscan_output_file (str): The filename of the WPScan output file."""
    command_str = ' '.join(command)
    command_list = command_str.split()
    logging.debug('Scanning domain %s... Scan started at %s with following command: %s', domain, SCAN_START_TIME, command_list)
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)
        logging.info(output)
        return wpscan_output_file, None, False
    except subprocess.CalledProcessError as e_process_err:
        logging.error("An error occurred while scanning domain '%s': %s", domain, e_process_err)
        output_json = None
        try:
            with open(wpscan_output_file, 'r', encoding="utf-8") as json_file:
                output_json = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            logging.error("json FileNotFoundError")
        if output_json:
            if "scan_aborted" in output_json:
                error_message = output_json.get("scan_aborted")
                if error_message in ERROR_STRINGS:
                    return wpscan_output_file, output_json, True  # API key error
            start_time = output_json.get("start_time")
            stop_time = output_json.get("stop_time")
            if start_time is not None and stop_time is not None:
                start_time_converted = datetime.fromtimestamp(float(start_time))
                stop_time_converted = datetime.fromtimestamp(float(stop_time))
                time_difference = stop_time_converted - start_time_converted
                human_readable_diff = format_timedelta(time_difference)
                return wpscan_output_file, human_readable_diff, False  # Successful scan
        return wpscan_output_file, "Unexpected JSON structure", True  # If neither scan_aborted nor start_time/stop_time are found, return a generic error

def process_domain(domain, api_keys, key_index):  # Scan domain with multiple API keys if needed
    api_key_error = True
    keys_tried = 0
    scan_results = []
    while api_key_error and keys_tried < len(api_keys):
        api_key = api_keys[key_index % len(api_keys)]
        filenames, output_json_or_error, api_key_error = run_wpscan(domain, api_key, key_index)
        for filename in filenames:
            scan_results.append((filename, output_json_or_error))
        if api_key_error:
            key_index += 1
            keys_tried += 1
    return scan_results, api_key_error

def send_email(config, recipient_emails, output_files, scan_results):  # Send email with attachments
    message = MIMEMultipart('alternative')
    message['From'] = f"Zen Alerts <{config['SENDER_EMAIL']}>"
    message['To'] = ', '.join(recipient_emails)
    message['Subject'] = f"WPScan | Website vulnerability scan results on {datetime.now().strftime(DATE_FORMAT)}"
    body_html = """<html><body><style>
    table {font-family: Arial, sans-serif;border-collapse: collapse;width: 100%;}
    th,td {border: 1px solid #ddd;padding: 8px;}
    th {padding-top: 12px;padding-bottom: 12px;text-align: left;background-color: #f2f2f2;color: #696969;}</style>"""
    body_html += """<p style="color: blue; font-size: 10px; font-family: 'Open Sans', Arial, sans-serif; font-style: italic;">Inbox is not monitored. Please do not reply back.</p>
    <p style="font-size: 12px; font-family: 'Open Sans', Arial, sans-serif;">WPscans have been completed for the below domains:</p>"""
    body_html += """<table border='1' cellpadding='5' style='font-size: 10px; font-family: 'Open Sans', Arial, sans-serif;'><tr>"""
    body_html += """<th style='background-color:#f2f2f2;color:#696969;'>Scanned Domains</th>"""
    body_html += """ <th style='background-color:#f2f2f2;color:#696969;'>Scan Duration</th></tr>"""
    body_text = """WPscans have been completed for the below domains:\n\n"""
    for filename, output_json_or_error in scan_results:
        if isinstance(output_json_or_error, str):
            body_html += f"<tr><td>{filename}</td><td>Scan Duration:{output_json_or_error} seconds</td><td>No error</td></tr>"
            body_text += f"Filename:{filename}, Scan Duration: {output_json_or_error} seconds, Error: No error\n"
        else:
            error = output_json_or_error.get("scan_aborted", "Unknown error")
            body_html += f"<tr><td>{filename}</td><td>{error}</td></tr>"
            body_text += f"Filename:{filename}, Scan failed, Error: {error}\n"
    body_html += """</table><br><p style="font-size: 12px; font-family: 'Open Sans', Arial, sans-serif;">Scan results has been attached for each domain.</p>"""
    body_html += """<p style="color: blue; font-size: 10px; font-family: 'Open Sans', Arial, sans-serif; font-style: italic;">Inbox is not monitored. Please do not reply back.</p><p style="color: blue; font-size: 10px; font-family: 'Open Sans', Arial, sans-serif; font-style: italic;">
This is an automated email. For app-related technical issues, contact <a href="mailto:ian@zenithpayments.com.au">Ian Menethil</a>.</p>
</body></html>"""
    body_text += """Attached, you will find the output files of the scans.
Inbox is not monitored. Please do not reply back.
This is an automated email. For app-related technical issues, contact ian@zenithpayments.com.au."""
    text_part = MIMEText(body_text, "plain")
    html_part = MIMEText(body_html, "html")
    message.attach(text_part)
    message.attach(html_part)
    logging.debug("Debug: All output files before attachments - %s", {output_files})
    for output_file in output_files:
        if not output_file:
            continue
        extension = os.path.splitext(output_file)[1]
        if extension not in ALLOWED_EXTENSIONS:
            continue
        try:
            with open(file=output_file, mode='rb') as file:
                file_contents = file.read()
                attachment = MIMEApplication(file_contents, Name=os.path.basename(output_file))
                attachment['Content-Disposition'] = f'attachment; filename="{os.path.basename(output_file)}"'
                message.attach(attachment)
            logging.debug("Attached file: %s", output_file)
        except FileNotFoundError as file_not_found_err:
            logging.error("Failed to read and attach file: %s. Error: %s", output_file, str(file_not_found_err))
        except PermissionError as permission_err:
            logging.error("Failed to read and attach file: %s. Error: %s", output_file, str(permission_err))
        except ValueError as value_err:
            logging.error("Failed due to a value error. Error: %s", str(value_err))
        except Exception as err_exception:  # pylint: disable=broad-except
            logging.error("Failed to read and attach file: %s. Error: %s", output_file, str(err_exception))
    try:
        with smtplib.SMTP(config['SMTPSERVER'], int(config['SMTPPORT']), local_hostname='localhost') as server:
            server.starttls()
            server.login(user=config['SENDER_EMAIL'], password=config['SENDER_PASSWORD'])
            server.sendmail(from_addr=config['SENDER_EMAIL'], to_addrs=recipient_emails, msg=message.as_string())
    except smtplib.SMTPException as error:
        logging.error("An error occurred while sending the email: %s", error)
    else:
        logging.info("Email sent with attachments.")

def scan_for_json_files():  # Scan directory for JSON files and convert them to CSV files
    json_files = [file for file in os.listdir(OUTPUT_DIRECTORY) if file.endswith(INPUT_FILE_EXTENSION)]
    if not json_files:
        logging.error("No JSON files found in this directory.")
        return
    logging.info('Scanning for JSON files in %s', OUTPUT_DIRECTORY)
    for json_file in json_files:
        logging.info('Found JSON file: %s', json_file)
        file_path = os.path.join(OUTPUT_DIRECTORY, json_file)
        with open(file_path, encoding='utf-8') as json_file:
            try:
                data = json.load(json_file)
            except json.JSONDecodeError:
                logging.error('Invalid JSON file: %s', json_file.name)
                continue
            csv_file_name = os.path.join(json_file.name[:-5] + ".csv")
            with open(csv_file_name, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                for key, value in data.items():
                    if isinstance(value, list):
                        writer.writerow([key, *value])
                    else:
                        writer.writerow([key, value])
                logging.info("File converted.")
    logging.info("All files converted.")

def archive_json_files():  # Archive JSON files
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)
    # Move all JSON files to the archive directory
    json_files = [file for file in os.listdir(OUTPUT_DIRECTORY) if file.endswith(INPUT_FILE_EXTENSION)]
    for json_file in json_files:
        source_path = os.path.join(OUTPUT_DIRECTORY, json_file)
        destination_path = os.path.join(ARCHIVE_DIR, json_file)
        os.rename(source_path, destination_path)
    logging.info("Archived %d JSON files to %s", len(json_files), ARCHIVE_DIR)

def main():  # Main function
    config = read_config_file()
    if config is None:
        logging.error("Error reading config file. Exiting.")
        return
    logging.info('Main started')
    email_option: bool = user_email_option()  # Get user email preference
    recipient_emails = get_email_recipients(config) if email_option else []  # Get recipient emails
    domains_to_scan = get_domains_to_scan(config)  # Get list of domains to scan
    scans_per_key = 1  # Use 1 key per scan
    api_keys = config['API_KEY_LIST']  # Scan each domain with multiple API keys if needed
    scan_results = []
    for i, domain in enumerate(domains_to_scan):  # Determine the API key to use based on the current domain index
        key_index, _ = divmod(i, scans_per_key)
        domain_scan_results = process_domain(domain, api_keys, key_index)  # Process the current domain and fetch the results
        scan_results.extend(domain_scan_results)  # Append the results to the main results list
    scan_for_json_files()  # Convert JSON files to CSV files
    if email_option:  # Delay for email attachments to be created
        time.sleep(10)
        output_files = [file for extension in ALLOWED_EXTENSIONS for file in glob.glob(OUTPUT_DIRECTORY + f'/*{extension}')]  # Fetch all the output files
        logging.info("Output files: %s", output_files)
        send_email(config, recipient_emails, output_files, scan_results)  # Send email with attachments
        logging.debug("Email sent %s %s %s", config, recipient_emails, scan_results)
    archive_json_files()  # Archive JSON files

if __name__ == '__main__':
    main()
