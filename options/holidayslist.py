import aiohttp
import asyncio
from django.http import JsonResponse
from django.utils import timezone
import jdatetime
from collections import defaultdict
from datetime import timedelta

async def fetch_holiday_info(session, date_str):
    url = f"https://holidayapi.ir/jalali/{date_str}"
    async with session.get(url) as response:
        return await response.json()

async def get_holidays(request):
    today = timezone.now().date()

    def convert_to_jalali(date):
        return jdatetime.date.fromgregorian(date=date).strftime('%Y/%m/%d')

    def get_future_dates(start_date, num_days):
        return [convert_to_jalali(start_date + timedelta(days=i)) for i in range(1, num_days + 1)]

    num_days = 10
    future_dates = get_future_dates(today, num_days)

    holidays = defaultdict(list)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_holiday_info(session, date) for date in future_dates]
        responses = await asyncio.gather(*tasks)

        for date, data in zip(future_dates, responses):
            is_holiday = data.get('is_holiday', False)
            if is_holiday:
                year, month, day = map(int, date.split('/'))
                holidays[month - 1].append(day)

    return JsonResponse(holidays)
