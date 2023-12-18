import requests
API_KEY = "2b3e28b6171933ae4bd783bf503b9250"
from pprint import pprint

END_POINT = "https://api.novaposhta.ua/v2.0/json/Address/getCities"
def get_info(town):
    data = {
        'apiKey': API_KEY,
        'modelName': 'Address',
        'calledMethod': 'getCities',
        'methodProperties': {
            'FindByString': town
        }
    }

    response = requests.post(END_POINT, json=data)

    if response.status_code == 200:
        city_data = response.json().get('data', [])

        selected_info = []

        for city in city_data:
            area_description = city.get('AreaDescription', '')
            city_description = city.get('Description', '')
            if area_description and city_description:
                area_and_city = f"{city_description.split('(')[0].strip()} ({area_description})"
                selected_info.append(area_and_city)

        return selected_info

    else:
        return None



def get_city_ref(town):
    data = {
        'apiKey': API_KEY,
        'modelName': 'Address',
        'calledMethod': 'searchSettlements',
        'methodProperties': {
            'CityName': town,
        }
    }

    try:
        response = requests.post(END_POINT, json=data)

        if response.status_code == 200:
            city_dict = response.json()
            if 'data' in city_dict and city_dict['data']:
                for city in city_dict['data']:
                    for item in city.get('Addresses', []):
                        if all(key in item for key in ('MainDescription', 'Area', 'Ref')):
                            result = item['Ref']
                            return result
                print("Місто не має адрес.")
            else:
                print("Місто не знайдено.")
        else:
            print(f"Помилка отримання референсу міста: {response.status_code}")
    except Exception as e:
        print(f"Помилка під час отримання референсу міста: {str(e)}")


def get_street_list(ref, street_name):
    data = {
        "apiKey": API_KEY,
        "modelName": "Address",
        "calledMethod": "searchSettlementStreets",
        "methodProperties": {
            "SettlementRef": ref,
            "StreetName": street_name,
            "Limit": "50"
        }
    }

    response = requests.post(END_POINT, json=data)

    if response.status_code == 200:
        result = response.json()
        return result
    else:
        print(f"Помилка отримання інформації: {response.status_code}")
        pprint(response.json())

def print_street_info(ref, street_name):
    street_list = get_street_list(ref, street_name)

    if street_list:
        streets = street_list.get('data', [])
        if streets:
            for street_info in streets[0].get('Addresses', []):
                if 'Present' in street_info:
                    return (street_info['Present'])
        else:
            print("Вулиць з вказаною адресою не знайдено.")
    else:
        print("Вулиць з вказаною адресою не знайдено.")


