# twister.py
import os
import subprocess
import logging
from typing import Tuple, Any
from rich.logging import RichHandler

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

logger = logging.getLogger()

ZenPay_domains = [
    "https://zenithpayments.com.au", "https://b2bpay.com.au", "https://travelpay.com.au", "https://rentalrewards.com.au",
    "https://schooleasypay.com.au", "https://thoroughbredpayments.com.au", "https://childcareeasypay.com.au"
]
SmartCentral_domains = ["https://askiris.com.au"]
TEST_ONLY_domains = ["https://ianmenethil.com", "https://wp.org"]
PrePaid_domains = [
    "https://giftcardregistry.com.au", "https://giftcardstore.com.au", "https://propertypay.com.au", "https://universalgiftcard.com.au"
]
domain_configurations = {"ZenPay": ZenPay_domains, "SmartCentral": SmartCentral_domains, "TEST ONLY": TEST_ONLY_domains, "PrePaid": PrePaid_domains}  # pylint: disable=line-too-long


def checkIfFileExists(outputfile) -> Any | str:
    # logger.info(f"Checking if {outputfile} exists...")
    base, ext = os.path.splitext(outputfile)
    counter = 1
    while os.path.isfile(outputfile):
        logger.info(f"{outputfile} exists.")
        outputfile = f"{base}_{counter}{ext}"
        counter += 1
    logger.info(f"Outputfile: {outputfile}")
    return outputfile


def run_dnstwist_for_domain(currentDomain, output_folder) -> None:
    allFuzzers = "*original,addition,bitsquatting,cyrillic,dictionary,homoglyph,hyphenation,insertion,omission,plural,repetition,replacement,subdomain,tld-swap,transposition,various,vowel-swap"  # pylint: disable=line-too-long
    dict_file = '_configs/zen.dict'
    tld_dict_file = '_configs/tld.dict'
    domain_name = currentDomain.split('//')[-1].split('.')[0]
    outputFile = os.path.join(output_folder, f"{domain_name}.csv")
    outputFile = checkIfFileExists(outputFile)
    screenshots_folder = output_folder + "screenshots"
    if not os.path.exists(screenshots_folder):
        os.makedirs(screenshots_folder)
    runTwister = [
        "dnstwist", "--all", "--banners", "--geoip", "--format", "csv", "--lsh", "tlsh", "--lsh-url", currentDomain, "--mxcheck", "--registered",
        "--phash", "--phash-url", currentDomain, "--screenshots", screenshots_folder, "--threads", "10", "--fuzzers", allFuzzers, "--nameservers",
        "8.8.8.8,1.1.1.1", "--dictionary", dict_file, "--tld", tld_dict_file, "--output", outputFile, currentDomain
    ]
    logger.info(f"Running DNSTwist for {domain_name} with output file {outputFile}")
    try:
        subprocess.run(runTwister, check=True)
        logger.info(f"DNSTwist executed successfully for {domain_name}.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to execute DNSTwist for {domain_name}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during execution of DNSTwist for {domain_name}: {e}")


def run_dnstwist(domain_list_name: str) -> None:
    domains = domain_configurations.get(domain_list_name, [])
    if not domains:
        logger.error(f"No domains found for the list name: {domain_list_name}")
        return
    output_folder = f"output/dnstwist/{domain_list_name}/"
    for currentDomain in domains:
        run_dnstwist_for_domain(currentDomain, output_folder)

    logger.info(f"DNSTwist executed successfully for all domains in {domain_list_name}.")


def main(domain_list_name) -> None:
    try:
        run_dnstwist(domain_list_name)
    except Exception as e:
        logger.error(f"An error occurred during execution: {e}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        logger.error("Domain list name not provided")
