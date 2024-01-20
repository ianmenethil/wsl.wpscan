# wrapper.py
import os
import subprocess
import logging
from typing import List, Tuple
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
# Create necessary directories
directories = [
    "output",
    "output/wpscan",
    # "output/wpscan/zenpay",
    # "output/wpscan/sc",
    # "output/wpscan/pre",
    # "output/wpscan/test",
    "output/dnstwist",
    # "output/dnstwist/zenpay",
    # "output/dnstwist/test",
    "output/wpwatcher-output",
    "logs"  # pylint: disable=line-too-long
]


# Function to create directories
def create_directories(dirs: List[str]) -> None:
    for directory in dirs:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created output directory {directory}")
        except OSError as e:
            logger.error(f"Failed to create output directory {directory}: {e}")


def main() -> None:
    try:
        create_directories(directories)
        chosen_domain = {
            "1": "ZenPay",
            "2": "SmartCentral",
            "3": "PrePaid",
            "4": "Scan All Sites",
            "9": "TEST ONLY"  # Add "TEST ONLY" option
        }.get(input("Enter the domain list to scan (1. ZenPay, 2. SmartCentral, 3. PrePaid, 4. Scan All Sites, 9. TEST ONLY): "), "")

        user_input = input("1. DNSTwist 2. WPScan 3. Both: ")

        if chosen_domain == "Scan All Sites":  # If "Scan All Sites" is selected
            if user_input in ["2", "3"]:
                for domain in ["ZenPay", "SmartCentral", "PrePaid"]:
                    subprocess.run(["python", "WPScanner.py", domain], check=True)
            if user_input in ["1", "3"]:
                for domain in ["ZenPay", "SmartCentral", "PrePaid"]:
                    subprocess.run(["python", "twister.py", domain], check=True)
        elif chosen_domain == "TEST ONLY":
            if user_input in ["1", "2", "3"]:
                # for domain in ["im.com", "wp.org"]:
                for domain in ["TEST ONLY"]:
                    subprocess.run(["python", "WPScanner.py", domain], check=True)
                    subprocess.run(["python", "twister.py", domain], check=True)
        else:
            if user_input == "1":
                subprocess.run(["python", "twister.py", chosen_domain], check=True)
            elif user_input == "2":
                subprocess.run(["python", "WPScanner.py", chosen_domain], check=True)
            elif user_input == "3":
                subprocess.run(["python", "WPScanner.py", chosen_domain], check=True)
                subprocess.run(["python", "twister.py", chosen_domain], check=True)
    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
