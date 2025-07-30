import requests
import csv
import time
from datetime import datetime

class LandRegistryClient:
    """
    Client for retrieving Price Paid Data (PPI transaction records)
    from HM Land Registry's Linked Data API (CSV interface).
    """
    BASE_URL = "https://landregistry.data.gov.uk/data/ppi/transaction-record.csv"

    def __init__(self, session=None, rate_limit_delay=0.0):
        """
        Initialize client with optional session and rate-limit delay.

        :param session: requests.Session or None for HTTP connection reuse
        :param rate_limit_delay: seconds to pause between paginated requests
        """
        self.session = session or requests.Session()
        self.rate_limit_delay = rate_limit_delay

    def get_transactions_by_date_range(self, from_date, to_date, start=0, limit=10000):
        """
        Generator yielding transaction records within a given date range.

        :param from_date: string or datetime in "YYYY-MM-DD"
        :param to_date: string or datetime in "YYYY-MM-DD"
        :param start: pagination start offset (default 0)
        :param limit: pagination limit per request (default 10000)
        :yields: dict representing each transaction row
        """
        # Convert datetime to string if necessary
        if isinstance(from_date, datetime):
            from_date = from_date.strftime('%Y-%m-%d')
        if isinstance(to_date, datetime):
            to_date = to_date.strftime('%Y-%m-%d')

        offset = start
        date_range_filter = f"{from_date}/{to_date}"

        while True:
            params = {
                'transactionDate': date_range_filter,
                '_start': offset,
                '_limit': limit
            }
            resp = self.session.get(self.BASE_URL, params=params)
            resp.raise_for_status()

            # Parse CSV content
            reader = csv.DictReader(resp.text.splitlines())
            rows = list(reader)
            if not rows:
                # no more results → stop iteration
                break

            for row in rows:
                yield row

            offset += len(rows)
            if self.rate_limit_delay > 0:
                time.sleep(self.rate_limit_delay)

    def fetch_all_in_date_range(self, from_date, to_date):
        """
        Return a complete list of transactions between two dates.

        :param from_date: string or datetime "YYYY-MM-DD"
        :param to_date: string or datetime "YYYY-MM-DD"
        :returns: list of dict rows (all matching transactions)
        """
        return list(self.get_transactions_by_date_range(from_date, to_date))
