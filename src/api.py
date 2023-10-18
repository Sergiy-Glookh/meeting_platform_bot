import requests
API_KEY = "2b3e28b6171933ae4bd783bf503b9250"

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




import requests



def get_streets(city_name):
    END_POINT = "https://api.novaposhta.ua/v2.0/json/Address/searchSettlementStreets"

    data = {
        'apiKey': API_KEY,
        'modelName': 'Address',
        'calledMethod': 'searchSettlementStreets',
        'methodProperties': {
            'CityName': city_name
        }
    }

    response = requests.post(END_POINT, json=data)

    if response.status_code == 200:
        street_data = response.json().get('data', [])

        selected_streets = []

        for street in street_data:
            street_description = street.get('Present', '')
            if street_description:
                selected_streets.append(street_description)

        return selected_streets

    else:
        return None
