# autoscanner.py
import os
import subprocess
import logging
from typing import List, Tuple
from rich.logging import RichHandler
import threading

# Configure rich logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M%p',
                    handlers=[
                        RichHandler(show_time=True,
                                    rich_tracebacks=True,
                                    markup=True,
                                    show_path=True,
                                    tracebacks_extra_lines=0,
                                    show_level=True,
                                    log_time_format='[%d-%m-%Y %I:%M%p]')
                    ])

DomainConfigPair = Tuple[str, str]


# Function to create directories
def create_directories(dirs: List[str]) -> None:
    for directory in dirs:
        try:
            os.makedirs(directory, exist_ok=True)
            # logging.info(f"Output directory {directory} created successfully.")
        except OSError as e:
            logging.error(f"Failed to create output directory {directory}: {e}")


# Prepaid domain and config files
payments_config_files = [
    "payments/zp.conf",
    "payments/b2b.conf",
    "payments/tp.conf",
    "payments/rr.conf",
    "payments/sep.conf",
    "payments/tbp.conf",
    "payments/cep.conf"  # pylint: disable=line-too-long
]
payments_domains = domains = [
    "https://zenithpayments.com.au", "https://b2bpay.com.au", "https://travelpay.com.au", "https://rentalrewards.com.au",
    "https://schooleasypay.com.au", "https://thoroughbredpayments.com.au", "https://childcareeasypay.com.au"
]
payments_domain_config_pairs = list(zip(payments_domains, payments_config_files))

# SC domain and config files

sc_domain_config_pairs = list(zip(sc_domains, sc_config_files))
# Test domain and config files

test_domain_config_pairs = list(zip(test_domains, test_config_files))

# Prepaid domain and config files

prepaid_domain_config_pairs = list(zip(prepaid_domains, prepaid_config_files))

# Domain configurations
domain_configurations = {
    "payments": list(zip(payments_domains, payments_config_files)),
    "sc": list(zip(sc_domains, sc_config_files)),
    "test": list(zip(test_domains, test_config_files)),
    "prepaid": list(zip(prepaid_domains, prepaid_config_files))
}

is_scanning = False

# Use threading.Lock for thread safety
is_scanning_lock = threading.Lock()


def run_wpwatcher(domain_list_name: str) -> None:
    global is_scanning
    try:
        with is_scanning_lock:
            is_scanning = True
        domain_config_pairs = domain_configurations.get(domain_list_name, [])
        output_folder = "output/" + domain_list_name + "/"
        group_name = domain_list_name.capitalize()

        for domain, config_file in domain_config_pairs:
            domain_name = domain.split('//')[-1].split('.')[0]
            domain_output_dir = os.path.join(output_folder, domain_name)
            try:
                os.makedirs(domain_output_dir, exist_ok=True)
                logging.info(f"{group_name}: Output directory for {domain_name} created successfully.")
            except OSError as e:
                logging.error(f"{group_name}: Failed to create output directory for {domain_name}: {e}")
                continue

            if not os.access(domain_output_dir, os.W_OK):
                logging.error(f"{group_name}: Insufficient permissions to write to output directory: {domain_output_dir}")
                continue

            try:
                subprocess.run(["wpwatcher", "--conf", f"configs/{config_file}"], check=True)
                logging.info(f"{group_name}: WPWatcher executed successfully for {domain_name}.")
            except subprocess.CalledProcessError as e:
                logging.error(f"{group_name}: Failed to execute WPWatcher for {domain_name}: {e}")
                continue
        logging.info(f"{group_name}: WPWatcher executed successfully for all domains.")
        is_scanning = False
    except Exception as e:
        logging.error(f"Failed to execute WPWatcher for {domain_list_name}: {e}")
    finally:
        with is_scanning_lock:
            is_scanning = False



create_directories(directories)

# Get user input for domain list
domain_list = input("Enter the domain list to scan (1. payments, 2. sc, 3. test, 4. prepaid): ")

if domain_list == "1":
    domain_list = "payments"
elif domain_list == "2":
    domain_list = "sc"
elif domain_list == "3":
    domain_list = "test"
elif domain_list == "4":
    domain_list = "prepaid"
else:
    print("Invalid selection. Please try again.")
