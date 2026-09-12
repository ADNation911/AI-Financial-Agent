import pandas as pd
import os

class DataLoader:
    def __init__(self, dataset_dir='dataset'):
        self.dataset_dir = dataset_dir
        self.profiles_path = os.path.join(dataset_dir, 'financial_profiles.csv')
        self.events_path = os.path.join(dataset_dir, 'financial_events.csv')
        self.exchange_path = os.path.join(dataset_dir, 'exchange_rates.csv')
        self.options_path = os.path.join(dataset_dir, 'request_payment_options.csv')
        self.messages_path = os.path.join(dataset_dir, 'messages.csv')
        self.images_path = os.path.join(dataset_dir, 'images.csv')
        self.requests_path = os.path.join(dataset_dir, 'requests.csv')
        
        self.df_profiles = pd.read_csv(self.profiles_path)
        self.df_events = pd.read_csv(self.events_path)
        self.df_exchange = pd.read_csv(self.exchange_path)
        self.df_options = pd.read_csv(self.options_path)
        self.df_requests = pd.read_csv(self.requests_path)

    def get_user_profile(self, user_id):
        match = self.df_profiles[self.df_profiles['user_id'] == user_id]
        if len(match) > 0:
            return match.iloc[0].to_dict()
        raise ValueError(f"User profile for {user_id} not found.")

    def get_user_events(self, user_id):
        return self.df_events[self.df_events['user_id'] == user_id]

    def get_request_payment_options(self, request_id):
        return self.df_options[self.df_options['request_id'] == request_id]

    def get_exchange_rate(self, amount, from_curr, to_curr, date_str):
        if from_curr == to_curr or amount == 0:
            return amount
            
        # Check direct conversion
        match = self.df_exchange[
            (self.df_exchange['from_currency'] == from_curr) & 
            (self.df_exchange['to_currency'] == to_curr)
        ]
        
        if len(match) > 0:
            # Match date or pick nearest
            date_match = match[match['rate_date'] == date_str]
            if len(date_match) > 0:
                rate = float(date_match.iloc[0]['rate'])
                return amount * rate
            else:
                rate = float(match.iloc[0]['rate'])
                return amount * rate

        # Check inverse conversion
        match_inv = self.df_exchange[
            (self.df_exchange['from_currency'] == to_curr) & 
            (self.df_exchange['to_currency'] == from_curr)
        ]
        if len(match_inv) > 0:
            date_match = match_inv[match_inv['rate_date'] == date_str]
            if len(date_match) > 0:
                rate = float(date_match.iloc[0]['rate'])
                return amount / rate
            else:
                rate = float(match_inv.iloc[0]['rate'])
                return amount / rate

        return amount
