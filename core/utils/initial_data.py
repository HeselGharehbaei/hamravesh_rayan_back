from cities.models import City, State, District
from payment.models import CreditCo, IncreaseWalletCo
from dispatcher.models import Dispatcher
from dispatcher_profile.models import DispatcherProfile, Zone_disp
from dispatcher_payment.models import IncreaseWalletCo as dispatcher_increasewalletco
from options.models import Size, Package, Value, Content, Service
from business.models import BusinessType
from django.conf import settings
import os
from django.core.files import File
from django.core.files.images import ImageFile
from django.db import IntegrityError
from django.db import models


current_directory = os.path.dirname(os.path.abspath(__file__))
small_image_path = os.path.join(current_directory, 'small.PNG')
medium_image_path = os.path.join(current_directory, 'medium.PNG')
big_image_path = os.path.join(current_directory, 'big.PNG')
pocket_image_path = os.path.join(current_directory, 'doc.PNG')
package_image_path = os.path.join(current_directory, 'box.PNG')

def create_coefitionts():
    creditco_amount = 0.1
    user_increasewalletco_amount = 0.05
    dispatcher_increasewalletco_amount = 0.2

    try:
        CreditCo.objects.update_or_create(defaults={'coefficient': creditco_amount})
        IncreaseWalletCo.objects.update_or_create(defaults={'Coefficient': user_increasewalletco_amount})
        dispatcher_increasewalletco.objects.update_or_create(defaults={'Coefficient': dispatcher_increasewalletco_amount})
        print("Coefficients updated/created successfully.")
    except Exception as e:
        print(f"Error updating/creating coefficients: {e}")


def create_package_dependency():
    sizes = {
        'small': {
            'title': 'کوچک',
            'description': 'حداکثر طول: 175 سانتی‌متر\nطول + دور ≤ 300 سانتی‌متر\nحداکثر وزن: 30 کیلوگرم',
            'price_co': 0.0,
            'image_path': small_image_path
        },
        'medium': {
            'title': 'متوسط',
            'description': 'حداکثر طول: 274 سانتی‌متر\nطول + دور ≤ 400 سانتی‌متر\nحداکثر وزن: 70 کیلوگرم',
            'price_co': 0.5,
            'image_path': medium_image_path
        },
        'big': {
            'title': 'بزرگ',
            'description': 'یک بعد می‌تواند بیش از 120 سانتی‌متر باشد (تا حداکثر 300 سانتی‌متر)\nحداکثر وزن: 70 کیلوگرم',
            'price_co': 0.8,
            'image_path': big_image_path
        }
    }

    sizes_instances = {}
    for key, size_data in sizes.items():
        try:
            with open(size_data['image_path'], 'rb') as img_file:
                django_image = ImageFile(img_file, name=os.path.basename(size_data['image_path']))
                size_instance, _ = Size.objects.update_or_create(
                    title=size_data['title'],
                    defaults={
                        'description': size_data['description'],
                        'price_co': size_data['price_co'],
                        'image': django_image
                    }
                )
                print(f"Size '{size_instance.title}' updated/created successfully.")
                sizes_instances[key] = size_instance

        except FileNotFoundError as e:
            print(f"Image file for '{size_data['title']}' does not exist: {size_data['image_path']} - Error: {e}")
        except Exception as e:
            print(f"Error updating/creating size '{size_data['title']}': {e}")

    packages = {
        'package': {
            'title': 'بسته',
            'short_description': 'بسته های تا ۵ کیلوگرم',
            'description': 'بسته های تا ۵ کیلوگرم',
            'icon_path': package_image_path
        },
        'pocket': {
            'title': 'پاکت',
            'short_description': 'شناسنامه و اسناد کاغذی',
            'description': 'شناسنامه و اسناد کاغذی',
            'icon_path': pocket_image_path
        }
    }

    for key, package_data in packages.items():
        try:
            with open(package_data['icon_path'], 'rb') as image_file:
                django_image = ImageFile(image_file, name=os.path.basename(package_data['icon_path']))
                package_instance, _ = Package.objects.update_or_create(
                    title=package_data['title'],
                    defaults={
                        'short_description': package_data['short_description'],
                        'description': package_data['description'],
                        'icon': django_image
                    }
                )
                package_instance.size.set(sizes_instances.values())
                print(f"Package '{package_instance.title}' updated/created successfully.")

        except FileNotFoundError as e:
            print(f"Icon file for '{package_data['title']}' does not exist: {package_data['icon_path']} - Error: {e}")
        except Exception as e:
            print(f"Error updating/creating package '{package_data['title']}': {e}")

def create_values():
    values = [
        (0, 1, 0.002),
        (1, 3, 0.002),
        (3, 5, 0.003)
    ]

    for min_value, max_value, coefficient in values:
        try:
            Value.objects.update_or_create(
                min_value=min_value,
                max_value=max_value,
                defaults={'coefficient': coefficient}
            )
            print(f"Value range ({min_value}, {max_value}) updated/created successfully.")
        except Exception as e:
            print(f"Error updating/creating value range ({min_value}, {max_value}): {e}")


def create_contents():
    contents = ['وسایل شکستنی', 'وسایل عمومی', 'سایر']

    for title in contents:
        try:
            Content.objects.update_or_create(title=title)
            print(f"Content '{title}' updated/created successfully.")
        except Exception as e:
            print(f"Error updating/creating content '{title}': {e}")


def create_businesstype():
    business_types = ['کتاب و لوازم التحریر', 'لوازم خانگی', 'مواد غذایی', 'مد و فشن', 'کامپیوتر و تجهیزات الکترونیکی', 'لوازم بهداشتی و آرایشی', 'تلفن و تجهیزات مخابراتی', 'یراق و ابزارآلات']

    for title in business_types:
        try:
            BusinessType.objects.update_or_create(title=title)
            print(f"Business type '{title}' updated/created successfully.")
        except Exception as e:
            print(f"Error updating/creating business type '{title}': {e}")


def create_city():
    try:
        City.objects.update_or_create(name='تهران')
        print("City 'Tehran' updated/created successfully.")
    except Exception as e:
        print(f"Error updating/creating city 'تهران': {e}")


def create_state():
    try:
        State.objects.update_or_create(name='تهران')
        print("State 'Tehran' updated/created successfully.")
    except Exception as e:
        print(f"Error updating/creating state 'تهران': {e}")


def create_services():
    services_data = [
        {
            'title': 'سرویس درون شهری - صبحگاهی',
            'hour': '07:45:00',
            'pickup_time': 'از ساعت ۸:۰۰ تا ساعت ۱۰:۰۰',
            'delivery_time': 'از ساعت ۱۰:۰۰ تا ساعت ۱۴:۰۰',
            'price': 75000,
            's_type': 'درون شهری',
            'count': 60
        },
        {
            'title': 'سرویس درون شهری - عصرگاهی',
            'hour': '13:45:00',
            'pickup_time': 'از ساعت ۱۴:۰۰ تا ساعت ۱۶:۰۰',
            'delivery_time': 'از ساعت ۱۶:۰۰ تا ساعت ۲۰:۰۰',
            'price': 95000,
            's_type': 'درون شهری',
            'count': 40
        },
        {
            'title': 'سرویس اختصاصی (با ما تماس بگیرید)',
            'hour': '07:45:00',
            'pickup_time': 'از ساعت ۸:۰۰ تا ساعت ۱۶:۰۰',
            'delivery_time': 'از ساعت ۱۰:۰۰ تا ساعت ۲۰:۰۰',
            'price': 0,
            's_type': 'درون شهری',
            'count': 0
        }
    ]

    for service_data in services_data:
        try:
            Service.objects.update_or_create(title=service_data['title'], defaults=service_data)
            print(f"Service '{service_data['title']}' updated/created successfully.")
        except Exception as e:
            print(f"Error updating/creating service '{service_data['title']}': {e}")


 
def create_free_disp():
    disp = Dispatcher.objects.update_or_create(username="آزاد")
    disp = Dispatcher.objects.filter(username="آزاد").first()
    profile = DispatcherProfile.objects.update_or_create(
    user=disp,
    first_name="آزاد_سیستم",
    last_name="آزاد_سیستم",
    phone_number="09123456789",  # Adjust based on the desired value
    address="آزاد_سیستم",
    birth_certificate_no="12345678901",
    national_code="1111111111",
    expiration_certificate_date="2025-12-31",  # Adjust based on the desired date
    guaranty_type="safte",  # Adjust based on the desired value
    confirm=True
)
    
def create_disp_zone():
    for i in range(1,7):
        Zone_disp.objects.update_or_create(
            zone_id=i
        )   

district_list={
'1':[
     "حصاربوعلی", "رستم آباد- فرمانیه", "اوین", "درکه", "زعفرانیه", "محمودیه", "ولنجک", 
    "امام زاده قاسم (ع)", "دربند", "گلابدره", "جماران", "دزاشیب", "نیاوران", "اراج", 
    "کاشانک", "شهرک دانشگاه", "شهرک نفت", "دارآباد", "باغ فردوس", "تجریش", "قیطریه", 
    "چیذر", "حکمت", "ازگل", "سوهانک", "شهید محلاتی", "اتوبان امام علی", "اتوبان صدر", 
    "اقدسیه", "الهیه – فرشته", "اندرزگو", "بلوار ارتش", "پارک وی", "تجریش", "جمشیدیه", 
    "دیباجی", "سعدآباد", "صاحبقرانیه", "فرمانیه", "قیطریه", "محمودیه", "مقدس اردبیلی", 
    "مینی سیتی", "نوبنیاد", "ولیعصر", "کاشانک", "کامرانیه"
],
'2':[
    "بوعلی", "سعادت‌آباد", "مدیریت", "کوهسار", "پونک", "شهید چوب‌تراش", "شهید خرم‌رودی", 
    "صادقیه شمالی شهرک هما", "صادقیه", "شهرآرا", "کوی نصر", "پردیسان", "شهرک آزمایش", 
    "تهران ویلا", "برق آلستوم", "تیموری", "طرشت", "همایونشهر", "توحید", "زنجان", "شادمهر", 
    "ایوانک", "دریا", "شهرک قدس", "آسمانها", "درختی", "فرحزاد", "مخابرات", "پرواز", "آزادی", 
    "اتوبان حکیم", "اتوبان شیخ فضل‌اله", "اتوبان محمد علی جناح", "اتوبان نیایش", "اتوبان یادگار امام", 
    "بهبودی", "جلال آل احمد", "خوش شمالی", "ستارخان", "شادمان", "شهرک ژاندارمری", "شهرک غرب", 
    "گیشا", "مترو شریف", "مرزداران"
],
'3':[
    "آرارات", "ونک", "امانیه", "زرگنده", "درب دوم", "رستم آباد و اختیاریه", 
    "داودیه", "سید خندان", "دروس", "قبا", "قلهک", "کاوسیه", "اختیاریه", 
    "پاسداران", "جردن", "جلفا", "خواجه عبداله", "دولت (کلاهدوز)", 
    "شیخ بهایی", "شیراز", "ظفر", "ملاصدرا", "میدان کتابی", 
    "میرداماد", "ولیعصر (بین پارک وی و نیایش)"
],
'4':[
    "مهران", "کاظم آباد", "کوهک", "مجیدیه و شمس آباد", "پاسداران و ضرابخانه",
    "حسین آباد و مبارک آباد", "شیان و لویزان", "علم و صنعت", "نارمک", "تهرانپارس غربی",
    "جوادیه", "خاک سفید", "تهرانپارس شرقی", "قاسم آباد و ده نارمک", "اوقاف",
    "شمیران نو", "حکیمیه", "قنات کوثر", "کوهسار", "مجید آباد", "اتوبان بابایی",
    "اتوبان باقری", "اتوبان صیاد شیرازی", "بنی هاشم", "پلیس", "دلاوران", "رسالت",
    "سراج", "شمس آباد", "شهدا", "صیاد شیرازی", "علم و صنعت", "فرجام", "لویزان",
    "میدان ملت", "هروی", "هنگام"
],
'5':[
    "شهران جنوبی", "شهران شمالی", "شهرزیبا", "اندیشه", "بهاران", "کن", "المهدی",
    "باغ فیض", "پونک جنوبی", "پونک شمالی", "حصارک", "شهرک نفت", "کوهسار", "مرادآباد",
    "پرواز", "سازمان برنامه جنوبی", "سازمان برنامه شمالی", "ارم", "سازمان آب", "اباذر",
    "فردوس", "مهران", "اکباتان", "بیمه", "آپادانا", "جنت آباد جنوبی", "جنت آباد شمالی",
    "جنت آباد مرکزی", "شاهین", "آیت الله کاشانی", "اشرفی اصفهانی", "ایران زمین شمالی",
    "بلوار تعاون", "بلوار فردوس", "بولیوار", "پونک", "پیامبر", "جنت آباد", 
    "سازمان برنامه", "ستاری", "سردار جنگل", "سولقان", "شهر زیبا", "شهران", 
    "شهرک اکباتان", "شهید مهدی باکری"
],
'6':[
    "نجات اللهی", "ایرانشهر", "پارک لاله", "کشاورز غربی", "نصرت", "۱۶ آذر", 
    "سنایی", "بهجت آباد", "عباس آباد", "قزل قلعه", "سیندخت", "گلها", "شیراز جنوبی", 
    "گاندی", "ساعی", "یوسف آباد", "جهاد", "جنت", "آرژانتین", "اتوبان همت", 
    "اسکندری", "امیر آباد", "بلوار کشاورز", "توانیر", "جمال زاده", "حافظ", 
    "زرتشت", "طالقانی", "فاطمی", "فلسطین", "میدان انقلاب اسلامی", "میدان ولیعصر", 
    "وزراء", "کارگر شمالی", "کردستان", "کریم خان"
],
'7':[
    "شارق الف", "دهقان", "شارق ب", "گرگان", "نظام آباد", "خواجه نصیر و حقوقی",
    "خواجه نظام شرقی", "خواجه نظام غربی", "کاج", "امجدیه خاقانی", "بهار",
    "سهروردی باغ صبا", "شهید قندی- نیلوفر", "عباس آباد- اندیشه", "حشمتیه", "دبستان",
    "ارامنه الف", "ارامنه ب", "قصر", "آپادانا", "امام حسین", "انقلاب", "خواجه نظام",
    "سرباز", "سهروردی", "شریعتی", "شهید مدنی", "شیخ صفی", "عباس آباد", "مدنی",
    "مرودشت", "مطهری", "مفتح جنوبی", "هفت تیر"
]

}

              
    



def main():
    create_coefitionts()
    create_package_dependency()
    create_businesstype()
    create_city()
    create_state()
    create_services()
    create_values()
    create_contents()
    create_free_disp()
    create_disp_zone()


if __name__ == '__main__':
    main()












