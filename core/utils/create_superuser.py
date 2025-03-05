from django.contrib.auth import get_user_model
import environ
from pathlib import Path
import os

env = environ.Env(
    DEBUG=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

def create_superuser():
    User = get_user_model()
    username = env('DJANGO_SUPERUSER_USERNAME')
    password = env('DJANGO_SUPERUSER_PASSWORD')
    email = env('DJANGO_SUPERUSER_EMAIL')
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username, 
            email=email, 
            password=password
        )
        print(f'Superuser {username} created.')
    else:
        print(f'Superuser {username} already exists.')
        
if __name__ == '__main__':
    create_superuser()

