"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_message_view(self):
        """Can we go to the message template to add a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/messages/new")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Add my message!", html)

    def test_message_no_user(self):
        """Reroute to home page with no user"""

        with self.client as c:
            resp = c.get("/messages/new", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_message_invalid_user(self):
        """Reroute to home page with invalid user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 987654

            resp = c.get("/messages/new", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_message_show(self):
        """Can you dipslay the message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            m = Message(text="Hello there", user_id=self.testuser.id)
            m.id = 1212
            db.session.add(m)
            db.session.commit()

            resp = c.get(f"/messages/{m.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello there", html)

    def test_message_destroy(self):
        """Can you delete a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            m = Message(text="Hello there", user_id=self.testuser.id)
            m.id = 2323
            db.session.add(m)
            db.session.commit()

            resp = c.post(f"/messages/{m.id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            count = Message.query.filter_by(id=m.id).count()

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(count, 0)
            self.assertIn("testuser", html)

    def test_msg_destroy_no_user(self):
        """No user logged in can not delete a message"""

        with self.client as c:
            m = Message(text="Hello there", user_id=self.testuser.id)
            m.id = 3434
            db.session.add(m)
            db.session.commit()

            resp = c.post(f"/messages/{m.id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', html)

    def test_msg_destroy_invalid_user(self):
        """Invalid user can not delete a message"""
        
        u2 = User.signup(username="testuser2",
                            email="test2@test.com",
                            password="testuser2",
                            image_url=None)
        u2.id = 87654
        db.session.add(u2)
        db.session.commit()

        m = Message(text="Hello there testuser", user_id=self.testuser.id)
        m.id = 5454
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 87654

            resp = c.post("/messages/5454/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
