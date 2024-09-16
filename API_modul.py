import requests
import csv
from urllib.parse import urlparse, urlunparse
from googletrans import Translator

def translate_text(text, target_language='ru'):
    translator = Translator()
    translated_text = translator.translate(text, dest=target_language)
    return translated_text.text
class APIModule:
    def __init__(self, api_key, db_connection, db_cursor):
        self.api_key = api_key
        self.url = "https://food-recipes-with-images.p.rapidapi.com/"
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "food-recipes-with-images.p.rapidapi.com"
        }
        self.db_connection = db_connection
        self.db_cursor = db_cursor

    def fetch_recipes(self, query):
        querystring = {"q": query}

        try:
            response = requests.get(self.url, headers=self.headers, params=querystring)
            response.raise_for_status()  # Вызывает исключение, если ответ сервера не успешен
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching recipes from API: {e}")
            return None

    def convert_to_csv(self, recipes_data):
        try:
            count_recipes_query = "SELECT COUNT(*) FROM recipes;"
            self.db_cursor.execute(count_recipes_query)
            current_count = self.db_cursor.fetchone()[0]

            if current_count >= 100:
                print(f"Limit reached. Not adding more recipes. Current count: {100}")
                return
            recipes = recipes_data['d']
            fieldnames = ['id', 'Title', 'Ingredients', 'Instructions', 'Image', 'description']

            with open('recipes.csv', 'w', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                csv_writer.writeheader()

                for recipe in recipes:
                    # Преобразование 'Ingredients' из словаря в список строк с номерами
                    ingredients_list = [f"{i}. {value}" for i, (_, value) in
                                        enumerate(recipe['Ingredients'].items(), start=1)]
                    ingredients_str = '\n'.join(ingredients_list)
                    recipe['Ingredients'] = ingredients_str

                    # Объединение 'Ingredients' и 'Instructions' в 'description'
                    recipe[
                        'description'] = f"Ingredients:\n{recipe['Ingredients']}\n\nInstructions: {recipe['Instructions']}"

                    # Приведение изображения к формату file_url
                    recipe['Image'] = f'https:{recipe["Image"]}'

                    csv_writer.writerow(recipe)

            return 'recipes.csv'
        except Exception as e:
            print(f"Error converting to CSV: {e}")
            return None

    def add_recipes_to_database(self, csv_filename):
        try:
            fieldnames = ['id', 'Title', 'Ingredients', 'Instructions', 'Image', 'description']
            with open(csv_filename, 'r', encoding='utf-8') as csvfile:
                csv_reader = csv.DictReader(csvfile)

                for row in csv_reader:
                    # Преобразование 'Ingredients' в словарь, если это строка
                    if isinstance(row['Ingredients'], str):
                        # Преобразование строки в словарь, предполагая, что элементы разделены запятыми
                        ingredients_dict = {str(i): value.strip() for i, value in
                                            enumerate(row['Ingredients'].split(','), start=1)}
                        row['Ingredients'] = ingredients_dict

                    # Преобразование 'Ingredients' из словаря в список строк с номерами
                    ingredients_list = [f"{i}. {value}" for i, (_, value) in
                                        enumerate(row['Ingredients'].items(), start=1)]
                    ingredients_str = '\n'.join(ingredients_list)
                    row['Ingredients'] = ingredients_str

                    # Объединение 'Ingredients' и 'Instructions' в 'description'
                    row['description'] = f"Ingredients:\n{row['Ingredients']}\n\nInstructions: {row['Instructions']}"

                    # Перевод 'description' на русский
                    translated_description = translate_text(row['description'])
                    row['description'] = translated_description

                    # Изменен запрос на добавление в базу данных
                    insert_recipe_query = "INSERT INTO recipes (title, description, photo_url) VALUES (%s, %s, %s);"
                    self.db_cursor.execute(insert_recipe_query, (
                        row['Title'], row['description'], row['Image']
                    ))

            self.db_connection.commit()
            print("Recipes added to the database successfully.")
        except Exception as e:
            print(f"Error adding recipes to the database: {e}")

    def fix_url_schema(url, default_scheme='https'):
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            # Если схема отсутствует, используем default_scheme
            fixed_url = urlunparse((default_scheme,) + parsed_url[1:])
        else:
            fixed_url = url
        return fixed_url

