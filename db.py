import aiosqlite


# Структура квиза


DB_NAME = 'quiz_bot.db'

async def create_table():
    # Создаем соединение с базой данных (если она не существует, то она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Выполняем SQL-запрос к базе данных
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS user_answers 
                    (user_id INTEGER, 
                    question_index INTEGER, 
                    is_question_right INTEGER,
                    PRIMARY KEY (user_id, question_index))''')
        # Сохраняем изменения
        await db.commit()

# Запускаем создание таблицы базы данных
# await create_table()
async def update_quiz_index(user_id, index):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index) VALUES (?, ?)', (user_id, index))
        # Сохраняем изменения
        await db.commit()

async def get_quiz_index(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0

async def add_user_answer(user_id, question_index, is_correct):
    """
    Add or update a user's answer in the database
    
    Args:
        user_id: The user's ID
        question_index: The index of the question
        is_correct: Boolean indicating if the answer was correct (True/False)
    """
    async with aiosqlite.connect(DB_NAME) as db:
        # Convert boolean to integer (SQLite doesn't have native boolean type)
        is_correct_int = 1 if is_correct else 0
        
        # Insert or replace the user's answer
        await db.execute('''INSERT OR REPLACE INTO user_answers 
                         (user_id, question_index, is_question_right) 
                         VALUES (?, ?, ?)''', 
                        (user_id, question_index, is_correct_int))
        
        # Save changes
        await db.commit()

async def get_user_answer(user_id, question_index):
    """
    Get a user's answer for a specific question
    
    Args:
        user_id: The user's ID
        question_index: The index of the question
    
    Returns:
        Boolean indicating if the answer was correct, or None if no answer exists
    """
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('''SELECT is_question_right FROM user_answers 
                              WHERE user_id = ? AND question_index = ?''', 
                             (user_id, question_index)) as cursor:
            result = await cursor.fetchone()
            if result:
                return bool(result[0])  # Convert integer back to boolean
            return None

async def get_user_score(user_id):
    """
    Get a user's total score (number of correct answers)
    
    Args:
        user_id: The user's ID
    
    Returns:
        Integer representing the number of correct answers
    """
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('''SELECT COUNT(*) FROM user_answers 
                              WHERE user_id = ? AND is_question_right = 1''', 
                             (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0

async def get_user_total_answers(user_id):
    """
    Get the total number of questions answered by a user
    
    Args:
        user_id: The user's ID
    
    Returns:
        Integer representing total answers
    """
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('''SELECT COUNT(*) FROM user_answers 
                              WHERE user_id = ?''', 
                             (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0



async def get_top_users_by_completion():
    """
    Return scores for all users who have answered the maximum number of questions
    
    Returns:
        List of tuples (user_id, score, total_answers) for users with max completion
    """
    async with aiosqlite.connect(DB_NAME) as db:
        # First, find the maximum number of answers any user has
        async with db.execute('''SELECT MAX(answer_count) 
                              FROM (SELECT user_id, COUNT(*) as answer_count 
                                    FROM user_answers 
                                    GROUP BY user_id)''') as cursor:
            max_answers_result = await cursor.fetchone()
            max_answers = max_answers_result[0] if max_answers_result and max_answers_result[0] is not None else 0
        
        if max_answers == 0:
            return []
        
        # Then get all users who have this maximum number of answers along with their scores
        async with db.execute('''SELECT ua.user_id, 
                              SUM(CASE WHEN ua.is_question_right = 1 THEN 1 ELSE 0 END) as score,
                              COUNT(*) as total_answers
                              FROM user_answers ua
                              GROUP BY ua.user_id
                              HAVING COUNT(*) = ?
                              ORDER BY score DESC, ua.user_id''', (max_answers,)) as cursor:
            results = await cursor.fetchall()
            return results

async def get_leaderboard(uid = None):
    """
    Return a leaderboard with all users sorted by score and completion
    
    Returns:
        List of tuples (user_id, score, total_answers) sorted by score descending
    """
    _where = f"WHERE user_id = {uid}" if uid is not None else ""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(f'''SELECT user_id, 
                              SUM(CASE WHEN is_question_right = 1 THEN 1 ELSE 0 END) as score,
                              COUNT(*) as total_answers
                              FROM user_answers 
                              {_where}
                              GROUP BY user_id
                              ORDER BY score DESC, total_answers DESC, user_id''') as cursor:
            results = await cursor.fetchall()
            return results

async def get_users_with_max_answers():
    """
    Alternative implementation: Get users with maximum answers using window function
    
    Returns:
        List of tuples (user_id, score, total_answers) for users with max completion
    """
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('''WITH user_stats AS (
                              SELECT user_id,
                              SUM(CASE WHEN is_question_right = 1 THEN 1 ELSE 0 END) as score,
                              COUNT(*) as total_answers
                              FROM user_answers 
                              GROUP BY user_id
                              )
                              SELECT user_id, score, total_answers
                              FROM user_stats
                              WHERE total_answers = (SELECT MAX(total_answers) FROM user_stats)
                              ORDER BY score DESC, user_id''') as cursor:
            results = await cursor.fetchall()
            return results

async def get_quiz_completion_stats():
    """
    Get statistics about quiz completion across all users
    
    Returns:
        Dictionary with completion statistics
    """
    async with aiosqlite.connect(DB_NAME) as db:
        # Get total number of questions (assuming you have a questions table)
        # If you don't have one, you might need to pass this as a parameter
        async with db.execute('''SELECT COUNT(DISTINCT question_index) FROM user_answers''') as cursor:
            total_questions_result = await cursor.fetchone()
            total_questions = total_questions_result[0] if total_questions_result else 0
        
        # Get user completion statistics
        async with db.execute('''SELECT 
                              COUNT(DISTINCT user_id) as total_users,
                              AVG(total_answers) as avg_completion,
                              MAX(total_answers) as max_completion
                              FROM (SELECT user_id, COUNT(*) as total_answers 
                                    FROM user_answers 
                                    GROUP BY user_id)''') as cursor:
            stats_result = await cursor.fetchone()
        
        return {
            'total_questions': total_questions,
            'total_users': stats_result[0] if stats_result else 0,
            'avg_completion': stats_result[1] if stats_result else 0,
            'max_completion': stats_result[2] if stats_result else 0
        }