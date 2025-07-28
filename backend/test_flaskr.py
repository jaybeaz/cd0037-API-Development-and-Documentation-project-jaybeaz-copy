import os
import unittest
from flaskr import create_app
from models import db, Question, Category
from settings import DB_USER, DB_PASSWORD, DB_HOST
import json


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.database_name = "trivia_test"
        
        self.database_path = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{self.database_name}"
        #self.database_path = f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}/{self.database_name}"

        # Create app with the test configuration
        self.app = create_app({
            "SQLALCHEMY_DATABASE_URI": self.database_path,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "TESTING": True
        })
        self.client = self.app.test_client()

        # Bind the app to the current context and create all tables
        with self.app.app_context():
            db.create_all()
            science = Category(type='Science')
            art = Category(type='Art')
            db.session.add_all([science, art])
            db.session.commit()
            q1 = Question(question='Test question 1', answer='Test answer 1',
                           category=art.id, difficulty=1)
            q2 = Question(question='Test question 2', answer='Test answer 2',
                           category=science.id, difficulty=2)
            q1.insert()
            q2.insert()

    def tearDown(self):
        """Executed after each test"""
        with self.app.app_context():
            db.session.remove()
            db.engine.execute('DROP TABLE IF EXISTS questions CASCADE')
            db.engine.execute('DROP TABLE IF EXISTS categories CASCADE')
            db.drop_all()

    """
    DONE
    Write at least one test for each test for successful operation and for expected errors.
    """

    def test_get_questions(self):
        """TEST GET method for /questions endpoint"""
        res = self.client.get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))
        self.assertTrue(data['categories'])

    def test_404_sent_requesting_beyond_valid_pagecount(self):
        """TEST GET method for /questions invalid page request 404"""
        res = self.client.get('/questions?page=10000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "resource not found")

    def test_delete_question(self):
        """TEST DELETE for /questions/id endpoint"""
        with self.app.app_context():
            question = Question.query.first()
            question_id = question.id

        res = self.client.delete(f'/questions/{question_id}')
        data = json.loads(res.data)
        with self.app.app_context():
            question = Question.query.filter(Question.id == question_id).one_or_none()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], question_id)
        self.assertEqual(question, None)

    def test_delete_404_if_question_nonexistant(self):
        """TEST DELETE for /questions/id gets 404 for nonexistant ID"""
        res = self.client.delete('/questions/10000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)

    def test_get_categories_endpoint(self):
        """TEST GET for /categories endpoint"""
        res = self.client.get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['categories']))

    def test_post_questions_creation(self):
        """TEST POST for /questions creation"""
        new_question = {
            "question": "What is the capital of California?",
            "answer": "Sacramento",
            "category": 1,
            "difficulty": 2
        }
        res = self.client.post('/questions', json=new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['created'])


    def test_post_questions_creation_400(self):
        """TEST POST for /questions creation 400, 404 and 422 errors"""
        incomplete_question = {
            "question": "What is the capital of California?",
            "answer": "Sacramento"
        }
        res = self.client.post('/questions', json=incomplete_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)


    def test_search_questions(self):
        """TEST POST for /questions search"""
        search_term = {
            "searchTerm": "Test"
        }
        res = self.client.post('/questions', json=search_term)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['questions']))


    def test_search_questions_invalid_term(self):
        """TEST POST for /questions search failures"""
        non_search_term = {
            "searchTerm": "nonexistentterm"
        }
        res = self.client.post('/questions', json=non_search_term)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['questions']), 0)

    def test_search_questions_malformed_request(self):
        """TEST POST /questions search with invalid data structure"""
        invalid_search = {
            "invalidKey": "some value"
        }
        
        res = self.client.post('/questions', json=invalid_search)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)

    def test_categories_question_filter(self):
        """TEST GET for /categories/category_id/questions filter"""
        res = self.client.get('/categories/1/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['questions']))
       

    def test_categories_question_filter_404_errors(self):
        """TEST GET for /categories/category_id/questions nonexistent category"""
        res = self.client.get('/categories/9999/questions')  # Category that doesn't exist
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_play_quiz_with_category(self):
        """Test POST /quizzes with specific category"""
        with self.app.app_context():
            category = Category.query.first()
            category_id = category.id
        
        quiz_data = {
            "previous_questions": [],
            "quiz_category": {"type": "Science", "id": category_id}
        }
        
        res = self.client.post('/quizzes', json=quiz_data)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['question'])
        self.assertEqual(data['question']['category'], category_id)

    def test_quizz_invalid_key(self):
        """Test POST /quizzes with malformed request"""
        quiz_data = {
            "previous_questions": [],
            "quiz_category": {"type": "Science", "id": "invalid_id_type"}  # String instead of int
        }
        
        res = self.client.post('/quizzes', json=quiz_data)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
