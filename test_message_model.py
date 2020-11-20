import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test model for messages"""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()

        u = User.signup("testuser", "test@test.com", "password", None)
        u.id = 1111
        self.uid = 1111

        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        m = Message(text="message for testuser", user_id=self.uid)
        m.id = 1212
        db.session.add(m)
        db.session.commit()

        mes = Message.query.get(1212)
        self.assertEqual(mes.text,"message for testuser")
        self.assertEqual(mes.user_id, self.uid)
        self.assertEqual(mes.user_id, mes.user.id)
        self.assertIsNotNone(mes.timestamp)

    def test_invalid_text(self):
        m = Message(user_id=1111)
        m.id = 2222
        db.session.add(m)
        with self.assertRaises(exc.IntegrityError) as e:
            db.session.commit()

    def test_invalid_user(self):
        m = Message(text="message for testuser")
        m.id = 3333
        db.session.add(m)
        with self.assertRaises(exc.IntegrityError) as e:
            db.session.commit()

    def test_message_likes(self):
        m1 = Message(text="message for testuser", user_id=self.uid)
        m1.id = 4444
        m2 = Message(text="another message for testuser", user_id=self.uid)
        m2.id = 5555
       
        u = User.signup("anotheruser", "anotheruser@user.com", "anotherpassword", None)
        u.id = 3434

        db.session.add_all([m1, m2, u])
        db.session.commit()

        u.likes.append(m1)
        db.session.commit()

        l = Likes.query.filter(Likes.user_id == u.id).all()
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].message_id, m1.id)