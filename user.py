class User:
    def __init__(self, user_id, username, password, conn, cursor):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.conn = conn
        self.cursor = cursor
    def check_recipes_on_moderation(self):
        # Логика для отправки рецепта на модерацию
        select_recipes_query = "SELECT id, title, description, photo_url FROM recipes_on_moderation WHERE user_id = %s;"
        self.cursor.execute(select_recipes_query, (self.user_id,))

        recipes = self.cursor.fetchall()
        return recipes
    def send_recipe_for_moderation(self, title, description, photo_url, chat_id):
        # Логика для отправки рецепта на модерацию
        insert_recipe_query = "INSERT INTO recipes_on_moderation (title, description, photo_url, user_id, approved, chat_id) VALUES (%s, %s, %s, %s, %s, %s);"
        self.cursor.execute(insert_recipe_query, (title, description, photo_url, self.user_id, False, chat_id))
        self.conn.commit()
    def get_recipe(self, recipe_id):
        # Логика для отправки рецепта на модерацию
        get_recipe_query = "SELECT title, description, photo_url FROM recipes WHERE id = %s;"
        self.cursor.execute(get_recipe_query, (recipe_id,))
        recipe_info = self.cursor.fetchone()
        return recipe_info
    def get_recipes_on_moderation(self):
        select_recipes_query = "SELECT id, title FROM recipes;"
        self.cursor.execute(select_recipes_query)
        recipes = self.cursor.fetchall()
        return recipes
    def serch_recipes(self, search_query):
        # Ищем рецепты по названию
        search_recipes_query = "SELECT id, title, description, photo_url FROM recipes WHERE LOWER(title) LIKE LOWER(%s);"
        self.cursor.execute(search_recipes_query, ('%' + search_query + '%',))
        search_results = self.cursor.fetchall()
        return search_results

# Пример использования:


