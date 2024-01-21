#!/bin/bash

config_files=(
    "prepaid/cpc.conf"
    "prepaid/gcr.conf"
    "prepaid/gcs.conf"
    # "prepaid/pp.conf"
    "prepaid/ugc.conf"
)
domains=(
    "https://corporateprepaidgiftcards.com.au"
    "https://giftcardregistry.com.au"
    "https://giftcardstore.com.au"
    # "https://propertypay.com.au" #not wpress
    "https://universalgiftcard.com.au"
)
outputFolder="output/pre/"
today=$(date +"%d%m%y")
mkdir -p output
mkdir -p output/scan_reports
mkdir -p output/scan_reports/zenpay
mkdir -p output/scan_reports/sc
mkdir -p output/scan_reports/pre
mkdir -p output/scan_reports/test
mkdir -p output/wpwatcher-output
mkdir -p logs

if [ $? -eq 0 ]; then
    echo "Output directory created successfully."
else
    echo "Error: Failed to create output directory."
    exit 1
fi
# Create backup folder if it doesn't exist
mkdir -p backup

# Copy output file to backup folder
# Enable error handling
set -e

# Loop through each domain and config file
for index in "${!domains[@]}"; do
    domain="${domains[$index]}"
    config_file="${config_files[$index]}"

    # Extract domain name for output
    domain_name=$(echo "$domain" | sed 's#https\?://##' | sed 's/\..*//')

    # Try executing WPWatcher command
    {
        wpwatcher --conf "configs/${config_file}"
        echo "WPWatcher executed successfully for ${domain_name}."
        echo "Scan finished for ${domain_name}."
        cp "${outputFolder}${domain_name}_${today}.txt" "backup/${domain_name}_${today}.txt"
        echo "Backup created for ${domain_name} in backup/${domain_name}_${today}.txt"
    } || {
        echo "Error: Failed to execute WPWatcher for ${domain_name}."
    }
done

# Disable error handling
set +e
