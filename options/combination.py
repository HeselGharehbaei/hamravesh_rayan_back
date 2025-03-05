import requests
from rest_framework.response import Response
from rest_framework.decorators import api_view
#comine two api(cities and service) to each other
@api_view()
def main(request):
    api_name = 'https://mohaddesepkz.pythonanywhere.com/'
    # Make requests to API 1
    response1 = requests.get(f'{api_name}cities/', headers={'Authorization': 'Bearer YOUR_API_KEY1'})
    data1 = response1.json()

    # Make requests to API 2
    response2 = requests.get(f'{api_name}options/services/', headers={'Authorization': 'Bearer YOUR_API_KEY2'})
    data2 = response2.json()

    # Combine or use the data as needed
    combined_data = {'data1': data1, 'data2': data2}

    # Your further processing logic goes here
    return Response(combined_data)
