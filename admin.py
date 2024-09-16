from user import User
class Admin(User):
    def __init__(self, user_id, username, password, conn, cursor):
        # Вызов конструктора родительского класса (User)
        super().__init__(user_id, username, password, conn, cursor)

    def check_recipes_on_moderation(self):
        # Логика для отправки рецепта на модерацию
        select_recipes_query = "SELECT id, title, description, photo_url FROM recipes_on_moderation;"
        self.cursor.execute(select_recipes_query)
        recipes = self.cursor.fetchall()
        return recipes

    def insert_approved_recipe(self, recipe_id):
        select_recipe_query = "SELECT title, description, user_id, photo_url FROM recipes_on_moderation WHERE id = %s;"
        self.cursor.execute(select_recipe_query, (recipe_id,))
        recipe = self.cursor.fetchone()
        answer, chat_id = None, None
        if recipe:
            title, description, user_id, photo_url = recipe

            # Получаем информацию о пользователе
            select_user_query = "SELECT chat_id FROM users WHERE id = %s;"
            self.cursor.execute(select_user_query, (user_id,))
            user_info = self.cursor.fetchone()

            if user_info:
                chat_id = user_info[0]
                # Вставляем рецепт в основную таблицу
                insert_recipe_query = "INSERT INTO recipes (title, description, user_id, photo_url) VALUES (%s, %s, %s, %s);"
                self.cursor.execute(insert_recipe_query, (title, description, user_id, photo_url))

                # Удаляем рецепт из таблицы на модерации
                delete_recipe_query = "DELETE FROM recipes_on_moderation WHERE id = %s;"
                self.cursor.execute(delete_recipe_query, (recipe_id,))

                # Уведомляем пользователя
                answer = f"Ваш рецепт '{title}' прошел модерацию и добавлен!"

        self.conn.commit()
        return answer, chat_id




