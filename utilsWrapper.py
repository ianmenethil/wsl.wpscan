# utilsWrapper.py
import subprocess
import logging
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

logger = logging.getLogger()  # pylint: disable=invalid-name


def main() -> None:
    try:
        action = {
            "1": "Create Reports",
            "2": "Send Reports",
            "3": "Both"
        }.get(input("Action to perform (1. Create Reports, 2. Send Reports, 3. Both): "), "")
        if action == "Create Reports":  # If "Create Reports" is selected
            subprocess.run(["python", "summarizeScans.py"], check=True)
        elif action == "Send Reports":  # If "Send Reports" is selected
            subprocess.run(["python", "mailer.py"], check=True)
        elif action == "Both":  # If "Both" is selected
            subprocess.run(["python", "summarizeScans.py"], check=True)
            subprocess.run(["python", "mailer.py"], check=True)
    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
