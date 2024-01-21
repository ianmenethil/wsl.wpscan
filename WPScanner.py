# WPScanner.py
import os
import subprocess
import logging
from typing import Tuple, Any
from rich.logging import RichHandler

# Configure rich logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M%p',
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
DomainConfigPair = Tuple[str, str]

logger = logging.getLogger()  # pylint: disable=invalid-name

# Define domain configurations
payments_config_files = [
    "payments/zp.conf",
    "payments/b2b.conf",
    "payments/tp.conf",
    "payments/rr.conf",
    "payments/sep.conf",
    "payments/tbp.conf",
    # "payments/pp.conf",
    "payments/cep.conf"  # pylint: disable=line-too-long
]

prepaid_config_files = ["prepaid/gcr.conf", "prepaid/gcs.conf", "prepaid/ugc.conf", "prepaid/cpc.conf", "prepaid/zaap.conf"]
test_config_files = ["test/im.conf", "test/wporg.conf"]
sc_config_files = ["sc/ai.conf"]
ZenPay_domains = [
    "https://zenithpayments.com.au", "https://b2bpay.com.au", "https://travelpay.com.au", "https://rentalrewards.com.au",
    "https://schooleasypay.com.au", "https://thoroughbredpayments.com.au", "https://childcareeasypay.com.au"
    # "https://propertypay.com.au" Not WP
]
SmartCentral_domains = ["https://askiris.com.au"]
TEST_ONLY_domains = ["https://ianmenethil.com", "https://wordpress.org"]
PrePaid_domains = [
    "https://giftcardregistry.com.au", "https://giftcardstore.com.au", "https://universalgiftcard.com.au", "https://corporateprepaidgiftcards.com.au",
    "https://zaap.com.au"
]
# Define domain configurations
domain_configurations = {
    "ZenPay": list(zip(ZenPay_domains, payments_config_files)),
    "SmartCentral": list(zip(SmartCentral_domains, sc_config_files)),
    "TEST ONLY": list(zip(TEST_ONLY_domains, test_config_files)),
    "PrePaid": list(zip(PrePaid_domains, prepaid_config_files))
}


def checkIfFileExists(outputfile) -> Any | str:
    logger.info(f"Checking if {outputfile} exists...")
    base, ext = os.path.splitext(outputfile)
    counter = 1
    while os.path.isfile(outputfile):
        logger.info(f"{outputfile} exists.")
        outputfile = f"{base}_{counter}{ext}"
        counter += 1
    logger.info(f"{outputfile} does not exist.")
    logger.info(f"Returning outputfile: {outputfile}")
    return outputfile


command = [r'C:\Ruby27-x64\bin\wpscan.bat', '--disable-tls-checks', '--update', '--cache-dir', './cache/']


def update_wpscan() -> bool:
    try:
        subprocess.run(command, shell=True, check=True)
        logger.info(f"WPScan updated successfully with {command}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to update WPScan: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to update WPScan: {e}")
        return False


# # Function to run WPWatcher for a given domain list
# def run_wpwatcher(domain_list_name: str) -> None:
#     logger.info(f"Received domain list {domain_list_name}")
#     try:
#         update_wpscan()
#     except subprocess.CalledProcessError as e:
#         logger.error(f"Failed to update WPWatcher: {e}")
#     try:
#         domain_config_pairs = domain_configurations.get(domain_list_name, [])
#         output_folder = f"output/{domain_list_name}/"
#         group_name = domain_list_name.capitalize()
#         for domain, config_file in domain_config_pairs:
#             domain_name = domain.split('//')[-1].split('.')[0]
#             domain_output_dir = os.path.join(output_folder, domain_name)
#             try:
#                 os.makedirs(domain_output_dir, exist_ok=True)
#                 logger.info(f"{group_name}: Output directory for {domain_name} created successfully.")
#             except OSError as e:
#                 logger.error(f"{group_name}: Failed to create output directory for {domain_name}: {e}")
#                 continue
#             if not os.access(domain_output_dir, os.W_OK):
#                 logger.error(f"{group_name}: Insufficient permissions to write to output directory: {domain_output_dir}")
#                 continue
#             try:
#                 subprocess.run(["wpwatcher", "--conf", f"_configs/{config_file}"], check=True)
#                 logger.info(f"{group_name}: WPWatcher executed successfully for {domain_name}.")
#             except subprocess.CalledProcessError as e:
#                 logger.error(f"{group_name}: Failed to execute WPWatcher for {domain_name}: {e}")
#                 continue
#         logger.info(f"{group_name}: WPWatcher executed successfully for all domains.")
#     except Exception as e:
#         logger.error(f"Failed to execute WPWatcher for {domain_list_name}: {e}")
# Function to run WPWatcher for a given domain list
def run_wpwatcher(domain_list_name: str) -> None:
    logger.info(f"Received domain list {domain_list_name}")
    try:
        update_wpscan()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to update WPWatcher: {e}")
    try:
        domain_config_pairs = domain_configurations.get(domain_list_name, [])
        output_folder = f"output/{domain_list_name}/"
        group_name = domain_list_name.capitalize()
        for domain, config_file in domain_config_pairs:
            domain_name = domain.split('//')[-1].split('.')[0]
            domain_output_dir = os.path.join(output_folder, domain_name)
            # try:
            #     os.makedirs(domain_output_dir, exist_ok=True)
            #     logger.info(f"{group_name}: Output directory for {domain_name} created successfully.")
            # except OSError as e:
            #     logger.error(f"{group_name}: Failed to create output directory for {domain_name}: {e}")
            #     continue
            if not os.access(domain_output_dir, os.W_OK):
                logger.error(f"{group_name}: Insufficient permissions to write to output directory: {domain_output_dir}")
                continue
            try:
                subprocess.run(["wpwatcher", "--conf", f"_configs/{config_file}"], check=True)
                logger.info(f"{group_name}: WPWatcher executed successfully for {domain_name}.")
            except subprocess.CalledProcessError as e:
                logger.error(f"{group_name}: Failed to execute WPWatcher for {domain_name}: {e}")
                continue
    except Exception as e:
        logger.error(f"Failed to execute WPWatcher for {domain_list_name}: {e}")
        logger.info(f"{group_name}: WPWatcher executed successfully for all domains.")


def main(domain_list_name) -> None:
    if not domain_list_name:
        logger.error("No domain list name provided.")
        return
    run_wpwatcher(domain_list_name)
    # copyAll = copyFilesFromSrcToDestDir(LOGDIR, EXCELDIR)
    # if copyAll:
    #     logger.info(f"Files copied successfully from {LOGDIR} to {EXCELDIR}")
    #     delAllFilesInDir(LOGDIR)
    #     logger.info(f"All files deleted from {LOGDIR}")
    # else:
    #     logger.error(f"Failed to copy files from {LOGDIR} to {EXCELDIR}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        logger.error("No domain list name provided.")
