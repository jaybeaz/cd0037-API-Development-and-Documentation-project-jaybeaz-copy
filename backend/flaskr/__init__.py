from flask import Flask, request, abort, jsonify
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def pagination_helper(request, selection):
    page = request.args.get("page", 1, type=int)
    questions_per_page = request.args.get("questions_per_page", QUESTIONS_PER_PAGE, type=int)
    start = (page - 1) * questions_per_page
    end = start + questions_per_page

    formatted_questions = [question.format() for question in selection]
    current_questions = formatted_questions[start:end]
    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True) # not sure if 2nd arg is necessary
    if test_config is None:
        setup_db(app)
    else:
        database_path = test_config.get('SQLALCHEMY_DATABASE_URI')
        setup_db(app, database_path=database_path)

    """
    @DONE: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, origins=['*']) #specifying origins arg here makes explicit but not necessary
    """
    @DONE: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def aftter_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type, Authorization"
        )
        response.headers.add(
            "Access-Control-Allow-Headers", "GET, POST, PATCH, DELETE, OPTIONS"
        )
        return response

    with app.app_context():
        db.create_all()

    """
    @DONE:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route('/categories', methods=["GET"])
    def get_categories():
        categories = Category.query.order_by(Category.id).all()
        formatted_categories = {category.id: category.type for category in categories}
        #[category.format() for category in categories]
        return jsonify(
            {
                "success": True,
                "categories": formatted_categories,
                "total": len(formatted_categories),
            }
        )


    """
    @DONE:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions', methods=["GET"])
    def get_questions():
        questions = Question.query.order_by(Question.id).all()
        current_questions = pagination_helper(request, questions)

        if len(current_questions) == 0:
            abort(404)

        categories = Category.query.order_by(Category.type).all()
        formatted_categories = {category.id: category.type for category in categories}

        return jsonify({
            "success": True,
            "questions": current_questions,
            "total_questions": len(questions),
            "current_category": None,
            "categories": formatted_categories
        })

    """
    @DONE:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route('/questions/<int:question_id>', methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()
            if question is None:
                abort(404)
            question.delete()

            return jsonify({
                "success": True,
                "deleted": question_id
            })
        except Exception as e:
            if hasattr(e, 'code') and e.code == 404:
                abort(404)
            else:
                abort(422)
        
    """
    @DONE:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    """
    @DONE:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route("/questions", methods=["POST"])
    def handle_questions_post():
        body = request.get_json()

        if "searchTerm" in body:
            search_term = body.get("searchTerm")
            search_pattern = f'%{search_term}%'
            try:
                questions = Question.query.filter(Question.question.ilike(search_pattern)).all()
                current_questions = pagination_helper(request, questions)

                categories = Category.query.order_by(Category.type).all()
                formatted_categories = {category.id: category.type for category in categories}                
                return jsonify({
                    "success": True,
                    "questions": current_questions,
                    "total_questions": len(questions),
                    "current_category": None,
                    "categories": formatted_categories
                })
            except Exception as e:
                abort(422)
        else:
            form_question = body.get("question", None)
            form_answer = body.get("answer", None)
            form_category = body.get("category", None)
            form_difficulty = body.get("difficulty", None)

            if not form_answer or not form_question or not form_category or not form_difficulty:
                abort(400)
            try:
                question = Question(answer=form_answer, question=form_question, category=form_category, difficulty=form_difficulty)
                question.insert()
                return jsonify({
                    "success": True,
                    "created": question.id
                })
            except Exception as e:
                abort(422)

    """
    @DONE:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route('/categories/<int:category_id>/questions', methods=["GET"])
    def get_questions_by_category(category_id):
        questions = Question.query.filter(Question.category == category_id).all()
        current_questions = pagination_helper(request, questions)

        category = Category.query.filter(Category.id == category_id).one_or_none()
        if category is None:
            abort(404)
        return jsonify({
                "success": True,
                "questions": current_questions,
                "total_questions": len(questions),
                "current_category": category.type,
            })

    """
    @DONE:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.route('/quizzes', methods=["POST"])
    def play_quiz():
        body = request.get_json()
        print("DEBUG - full request body: ", body)
        
        previous_questions = body.get('previous_questions', [])
        quiz_category = body.get('quiz_category', None)

        try:
            if quiz_category and quiz_category['id'] != 0:
                questions = Question.query.filter(Question.category == quiz_category['id']).all()
            else:
                questions = Question.query.all()
            remaining_questions = [q for q in questions if q.id not in previous_questions]
            if remaining_questions:
                current_question = random.choice(remaining_questions).format()
            else:
                current_question = None

            return jsonify({
                "success": True,
                "question": current_question
            })
        
        except:
            abort(422)

    """
    @DONE:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "message": "bad request",
            "error": "400"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "message": "resource not found",
            "error": "404"
        }), 404
    
    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "message": "unprocessable",
            "error": "422"
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "message": "internal server error",
            "error": "500"
        }), 500

    return app

