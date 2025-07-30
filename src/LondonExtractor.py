import csv
import os

class LondonFilter:
    """
    Reads all 'pp-<year>.csv' files in a directory, keeps only rows
    where the town/city field is exactly 'LONDON' (case‑insensitive),
    and appends them into a single 'london.csv' output file.
    
    Assumes files are comma-delimited, no header row,
    with fields in the expected 16-column order:
    (transaction_id, price, transfer_date, postcode, property_type, old_new,
     duration, paon, saon, street, locality, town, district, county,
     ppd_category, record_status)
    """
    COLUMN_COUNT = 16
    TOWN_IDX = 11  # zero-based index: 12th column is Town/City

    def __init__(self, input_dir, output_path="london.csv"):
        """
        :param input_dir: directory containing pp-{year}.csv files
        :param output_path: filepath for merged output (defaults to london.csv)
        """
        self.input_dir = input_dir
        self.output_path = output_path

    def _is_london(self, row):
        """
        Check if the row's Town/City column is 'LONDON' (case-insensitive).
        """
        return len(row) >= self.TOWN_IDX + 1 and row[self.TOWN_IDX].strip().upper() == "LONDON"

    def process(self):
        """
        Iterate through input files, filter London rows, and write to output file.
        """
        # Open output once and write as CSV
        with open(self.output_path, "w", newline="", encoding="utf-8") as out_f:
            writer = csv.writer(out_f)
            # Optionally write a header row if desired:
            header = [
                "transaction_id", "price", "transfer_date", "postcode", "property_type",
                "old_new", "duration", "paon", "saon", "street",
                "locality", "town", "district", "county", "ppd_category", "record_status"
            ]
            writer.writerow(header)

            # Loop through all files named pp-<year>.csv
            for fname in sorted(os.listdir(self.input_dir)):
                if not fname.lower().startswith("pp-") or not fname.lower().endswith(".csv"):
                    continue
                path = os.path.join(self.input_dir, fname)
                with open(path, newline="", encoding="utf-8") as in_f:
                    reader = csv.reader(in_f)
                    for row in reader:
                        # Skip any row with unexpected column count
                        if len(row) != self.COLUMN_COUNT:
                            continue
                        if self._is_london(row):
                            writer.writerow(row)

        print(f"Filtered London data saved to: {self.output_path}")
