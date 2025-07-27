import os
import unittest

from flaskr import create_app
from models import db, Question, Category
import json


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.database_name = "trivia_test"
        self.database_user = "postgres"
        self.database_password = "password"
        self.database_host = "localhost:5432"
        self.database_path = f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}/{self.database_name}"

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
            category = Category(type='Science')
            db.session.add(category)
            db.session.commit()
            q1 = Question(question='Test question 1', answer='Test answer 1',
                           category=category.id, difficulty=1)
            q2 = Question(question='Test question 2', answer='Test answer 2',
                           category=category.id, difficulty=2)
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
    TODO
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

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
