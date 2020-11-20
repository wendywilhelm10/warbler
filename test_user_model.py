# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

# db.drop_all()
db.create_all()

class UserModelTestCase(TestCase):
    """Test model for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        u1 = User.signup("testuser1", "test1@test.com", "password1", None)
        u1.id = 1111
        uid1 = 1111

        u2 = User.signup("testuser2", "test2@test.com", "password2", None)
        u2.id = 2222
        uid2 = 2222
        
        db.session.commit()

        self.u1 = User.query.get(uid1)
        self.u2 = User.query.get(uid2)
        self.uid1 = uid1
        self.uid2 = uid2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_print(self):
        """ Does printing the user work?"""
        self.assertEqual(f"{self.u1}", "<User #1111: testuser1, test1@test.com>")

    def test_user_follows(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u2.following), 0)

        self.assertEqual(self.u1.following[0].id, self.u2.id)
        self.assertEqual(self.u2.followers[0].id, self.u1.id)

    def test_is_following(self):
        """Does is_following returns True when user1 following user2?
           Does is_following returns False when user2 is not following user1?
        """

        # f = Follows(user_being_followed_id=self.uid1, 
        #             user_following_id=self.uid2)
        # db.session.add(f)
        # db.session.commit()

        # u1 = User.query.get(self.uid1)
        # u2 = User.query.get(self.uid2)
        # self.assertTrue(u2.is_following(u1))
        # self.assertFalse(u1.is_following(u2))

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        """Does is_followed_by returns True when user2 is followed by user2?
           Does is_followed_by returns False when user1 is not followed by user2?
        """
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

    def test_invalid_username(self):
        invalid = User.signup(None, "test@test.com", "password", None)
        with self.assertRaises(IntegrityError) as e:
            db.session.commit()

    def test_invalid_email(self):
        invalid = User.signup("testuser", None, "password", None)
        with self.assertRaises(IntegrityError) as e:
            db.session.commit()

    def test_invalid_password(self):
        with self.assertRaises(ValueError) as e:
            User.signup("testuser", "test@test.com", None, None)

        with self.assertRaises(ValueError) as e:
            User.signup("testuser", "test@test.com", "", None)

    def test_valid_signup(self):
        user = User.signup("testuser", "test@test.com", "password", None)
        user.id = 1212
        db.session.add(user)
        db.session.commit()

        test_user = User.query.get(1212)
        self.assertEqual(test_user.username, "testuser")
        self.assertEqual(test_user.email, "test@test.com")
        self.assertEqual(test_user.image_url, "/static/images/default-pic.png")
        self.assertNotEqual(test_user.password, "password")
        self.assertTrue(test_user.password.startswith("$2b$"))

    def test_authenticate(self):
        user = User.authenticate("testuser1", "password1")
        self.assertEqual(self.u1, user)

    def test_authenticate_false(self):
        self.assertFalse(User.authenticate("testuser1", "abcdefg"))

    def test_same_username(self):
        invalid = User.signup("testuser1", "test11@test.com", "password", None)
        with self.assertRaises(IntegrityError) as e:
            db.session.commit()

    def test_same_email(self):
        invalie = User.signup("test", "test1@test.com", "password", None)
        with self.assertRaises(IntegrityError) as e:
            db.session.commit()