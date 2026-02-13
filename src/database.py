from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import datetime, date

load_dotenv()


class Database:

    def __init__(self):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')

        if not url or not key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env")

        self.client: Client = create_client(url, key)
        print("✅ Connected to Supabase")

    def save_meal(self, meal_data: dict) -> dict:
        record = {
            'meal_type': meal_data['meal_type'],
            'foods': meal_data['foods'],
            'protein': meal_data['protein'],
            'carbs': meal_data['carbs'],
            'fats': meal_data['fats'],
            'calories': (meal_data['protein'] * 4) +
                        (meal_data['carbs'] * 4) +
                        (meal_data['fats'] * 9),
            'notes': meal_data.get('notes', ''),
            'raw_input': meal_data.get('raw_input', ''),
        }

        response = self.client.table('meals').insert(record).execute()
        return response.data[0] if response.data else None

    def get_meals_today(self) -> list:
        today = date.today().isoformat()

        response = (
            self.client.table('meals')
            .select('*')
            .gte('created_at', f'{today}T00:00:00')
            .lte('created_at', f'{today}T23:59:59')
            .order('created_at')
            .execute()
        )

        return response.data or []

    def get_meals_last_n_days(self, n: int = 7) -> list:
        from datetime import timedelta
        start_date = (datetime.now() - timedelta(days=n)).isoformat()

        response = (
            self.client.table('meals')
            .select('*')
            .gte('created_at', start_date)
            .order('created_at', desc=True)
            .execute()
        )

        return response.data or []

    def save_daily_log(self, log_data: dict) -> dict:
        response = self.client.table('daily_logs').insert(log_data).execute()
        return response.data[0] if response.data else None

    def get_daily_logs_last_n_days(self, n: int = 7) -> list:
        from datetime import timedelta
        start_date = (datetime.now() - timedelta(days=n)).isoformat()

        response = (
            self.client.table('daily_logs')
            .select('*')
            .gte('created_at', start_date)
            .order('created_at', desc=True)
            .execute()
        )

        return response.data or []

    def get_daily_macro_totals(self) -> dict:
        meals = self.get_meals_today()

        totals = {
            'protein': sum(m['protein'] for m in meals),
            'carbs': sum(m['carbs'] for m in meals),
            'fats': sum(m['fats'] for m in meals),
            'calories': sum(m['calories'] for m in meals),
            'meal_count': len(meals)
        }

        return totals
