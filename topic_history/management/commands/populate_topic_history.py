import os
import pandas as pd
import json
from django.core.management.base import BaseCommand
from topic_history.models import Topic, TopicHistory
from django.db import transaction

class Command(BaseCommand):
    help = "Populate TopicHistory with data from Excel files in a specified directory."

    def add_arguments(self, parser):
        parser.add_argument(
            '--directory', type=str, required=True,
            help="Directory containing yearly Excel files named like '2013.xlsx', '2014.xlsx', etc."
        )

    def handle(self, *args, **options):
        directory = options['directory']
        
        # List all Excel files in the directory
        files = [f for f in os.listdir(directory) if f.endswith('.xlsx')]
        
        # Start a transaction for database operations
        with transaction.atomic():
            for file_name in files:
                # Extract the year from the file name
                year = file_name.split('.')[0]
                
                # Load the Excel file
                file_path = os.path.join(directory, file_name)
                data = pd.read_excel(file_path)
                
                # Standardize column names and drop any header rows if needed
                data.columns = ["Ders", "Konu", "SSM_KODU", "TYT", "AYT", "MSU", "ALES", "YDT", "KPSS", "LYS", "YGS"]
                data = data.drop(0).set_index("SSM_KODU").dropna(how="all")
                
                # Retain only relevant columns and fill NaN with zeros
                data = data[["TYT", "AYT", "MSU", "ALES", "YDT", "KPSS", "LYS", "YGS"]].fillna(0).astype(int)
                
                # Iterate over each row in the Excel file
                for ssm_kodu, row in data.iterrows():
                    # Convert `ssm_kodu` to integer
                    try:
                        ssm_kodu = int(ssm_kodu)
                    except ValueError:
                        print(f"Invalid SSM KODU: {ssm_kodu}. Skipping.")
                        continue
                    
                    # Try to retrieve the Topic by achievement_code
                    try:
                        topic = Topic.objects.get(achievement_code=ssm_kodu)
                    except Topic.DoesNotExist:
                        print(f"Topic with SSM KODU {ssm_kodu} does not exist.")
                        continue
                    
                    # Retrieve or initialize TopicHistory entry
                    topic_history, created = TopicHistory.objects.get_or_create(topic=topic)

                    # Load existing history_data or initialize if it doesn't exist
                    history_data = topic_history.history_data if topic_history.history_data else {}

                    # Add or update the data for the current year
                    history_data[year] = {
                        "TYT": str(row["TYT"]),
                        "AYT": str(row["AYT"]),
                        "MSU": str(row["MSU"]),
                        "ALES": str(row["ALES"]),
                        "YDT": str(row["YDT"]),
                        "KPSS": str(row["KPSS"]),
                        "LYS": str(row["LYS"]),
                        "YGS": str(row["YGS"])
                    }

                    # Update the history_data field with accumulated yearly data
                    topic_history.history_data = history_data
                    topic_history.save()

                self.stdout.write(self.style.SUCCESS(f"Processed {file_name} and updated TopicHistory records."))
                
        self.stdout.write(self.style.SUCCESS("All files processed and data inserted successfully."))
