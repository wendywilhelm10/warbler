"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows, Likes

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


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):

        db.drop_all()
        db.create_all()

        User.query.delete()
        Follows.query.delete()
        Message.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        self.u1 = User.signup("testuser", "test@test.com", "testuser", None)
        self.u1.id = 1212

        self.u2 = User.signup("testuser2", "test2@test.com", "testuser2", None)
        self.u2.id = 2323

        db.session.add_all([self.u1, self.u2])
        db.session.commit()

    def test_list_users(self):
        """Do all users get listed?"""

        with self.client as c:
            resp = c.get("/users")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser', html)
            self.assertIn('testuser2', html)

    def test_show_users(self):
        """Do messages show up for user?"""

        with self.client as c:
            m1 = Message(id=1111, text="first text for user", user_id=1212)
            m2 = Message(id=2222, text="second text for user", user_id=1212)

            db.session.add_all([m1, m2])
            db.session.commit()

            resp = c.get(f"/users/{self.u1.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('first text for user', html)
            self.assertIn('second text for user', html)
            self.assertIn('testuser', html)

    def setup_follows(self):
        u3 = User.signup("testuser3", "test3@test.com", "password3", None)
        u3.id = 4545
        u4 = User.signup("abcdef", "abcdefg@test.com", "password4", None)
        u4.id = 5656
        
        db.session.add_all([u3, u4])
        db.session.commit()

        f1 = Follows(user_being_followed_id=u3.id, user_following_id=self.u1.id)
        f1.id = 11
        f2 = Follows(user_being_followed_id=u4.id, user_following_id=self.u1.id)
        f2.id = 22
        f3 = Follows(user_being_followed_id=self.u1.id, user_following_id=self.u2.id)
        f3.id = 33
        f4 = Follows(user_being_followed_id=self.u1.id, user_following_id=u4.id)
        f4.id = 44

        db.session.add_all([f1, f2, f3, f4])
        db.session.commit()

    def test_show_following(self):
        """Do users this user is following show up?"""

        self.setup_follows()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            resp = c.get(f"/users/{self.u1.id}/following")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser', html)
            self.assertIn('@abcdef', html)
            self.assertNotIn('@testuser2', html)

    def test_show_following_no_user(self):
        """Does page redirect to / when no user?"""

        with self.client as c:
            resp = c.get(f"/users/{self.u1.id}/following", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_show_followers(self):
        """Do users following this user show up?"""

        self.setup_follows()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id  

            resp = c.get(f"/users/{self.u1.id}/followers")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser2", html)
            self.assertIn("@abcdef", html)
            self.assertNotIn('@testuser3', html)

    def test_show_followers_no_user(self):
        """Does page redirect to / when no user?"""

        with self.client as c:
            resp = c.get(f"/users/{self.u1.id}/followers", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_show_likes(self):
        """Does messages the user liked show up?"""

        u3 = User.signup("testuser3", "test3@test.com", "password3", None)
        u3.id = 4545
        u4 = User.signup("abcdef", "abcdefg@test.com", "password4", None)
        u4.id = 5656

        db.session.add_all([u3, u4])
        db.session.commit()

        m1 = Message(text='message one for testuser1', user_id=1212)
        m1.id = 111
        m2 = Message(text='message one for testuser2', user_id=2323)
        m2.id = 222
        m3 = Message(text='message two for testuser2', user_id=2323)
        m3.id = 333
        m4 = Message(text='message one for testuser3', user_id=4545)
        m4.id = 444
        m5 = Message(text='message one for abcdef', user_id=5656)
        m5.id = 555

        db.session.add_all([m1, m2, m3, m4, m5])
        db.session.commit()

        l1 = Likes(user_id=1212, message_id=222)
        l1.id = 12
        l2 = Likes(user_id=1212, message_id=444)
        l2.id = 34
        l3 = Likes(user_id=1212, message_id=555)
        l3.id = 45

        db.session.add_all([l1, l2, l3])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            resp = c.get(f"/users/{self.u1.id}/likes")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('message one for testuser2', html)
            self.assertIn('message one for testuser3', html)
            self.assertIn('message one for abcdef', html)
            self.assertNotIn('message one for testuser1', html)
            self.assertNotIn('message two for testuser2', html)

    def test_show_likes_no_user(self):
        """Does page redirect to / when no user?"""

        with self.client as c:
            resp = c.get(f"/users/{self.u1.id}/likes", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_add_follow(self):
        """Does user you want to follow appear?"""

        u3 = User.signup("abcdef", "abcdefg@test.com", "password4", None)
        u3.id = 5656

        db.session.add(u3)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            u = User.query.get(5656)
            resp = c.post(f"/users/follow/{u.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@abcdef", html)
            self.assertNotIn('@testuser2', html)

    def test_add_follow_no_user(self):
        """Does page redirect to / when no user?"""

        with self.client as c:
            resp = c.post(f"/users/follow/{self.u2.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_stop_following(self):
        """Does user you want to stop following not appear?"""

        u3 = User.signup("abcdef", "abcdefg@test.com", "password4", None)
        u3.id = 5656

        db.session.add(u3)
        db.session.commit()

        f1 = Follows(user_being_followed_id=u3.id, user_following_id=self.u1.id)
        f1.id = 11
        f2 = Follows(user_being_followed_id=self.u2.id, user_following_id=self.u1.id)
        f2.id = 22

        db.session.add_all([f1, f2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            u = User.query.get(2323)
            resp = c.post(f"/users/stop-following/{u.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@abcdef', html)
            self.assertNotIn('@testuser2', html)

    def test_stop_following_no_user(self):
        """Does page redirect to / when no user?"""

        with self.client as c:
            resp = c.post(f"/users/stop-following/{self.u2.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_profile_get(self):
        """Does profile show up for user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            resp = c.get("/users/profile")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Edit Your Profile", html)
            self.assertIn("(Optional) Bio", html)

    def test_delete_user(self):
        """Does user get deleted?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2.id

            resp = c.post("/users/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            u_cnt = User.query.filter_by(id=self.u2.id).count()
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(u_cnt, 0)
            self.assertIn('Join Warbler today', html)
            
    def test_delete_no_user(self):
        """Does page redirect to / when no user?"""

        with self.client as c:
            resp = c.post(f"/users/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_like_message(self):
        """Does liking a message display the star?"""

        f = Follows(user_being_followed_id=self.u1.id, user_following_id=self.u2.id)
        db.session.add(f)
        db.session.commit()

        m = Message(text="I am being followed by somebody", user_id=self.u1.id)
        m.id = 2121
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2.id

            resp = c.post('/users/add_like/2121', follow_redirects=True)
            html = resp.get_data(as_text=True)

            l_cnt = Likes.query.filter_by(user_id=self.u2.id).count()
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(l_cnt, 1)
            self.assertIn('fa fa-star', html)
            self.assertNotIn('fa fa-thumbs-up', html)

    def test_like_message_no_user(self):
        """Does page redirect to / when no user?"""

        with self.client as c:
            resp = c.post('/users/add_like/2121', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Unauthorized, can not add like.", html)

    def test_unlike_message(self):
        """Does unliking a message move star and show thumbs up?"""

        f = Follows(user_being_followed_id=self.u1.id, user_following_id=self.u2.id)
        db.session.add(f)
        db.session.commit()

        m = Message(text="I am being followed by somebody", user_id=self.u1.id)
        m.id = 2121
        db.session.add(m)
        db.session.commit()

        l = Likes(user_id=self.u2.id, message_id=2121)
        db.session.add(l)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2.id

            resp = c.post('/users/unlike/2121', follow_redirects=True)
            html = resp.get_data(as_text=True)

            l_cnt = Likes.query.filter_by(user_id=self.u2.id).count()
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(l_cnt, 0)
            self.assertIn('fa fa-thumbs-up', html)
            self.assertNotIn('fa fa-star', html)
            
    def test_unlike_message_no_user(self):
        """Does page redirect to / when no user?"""

        with self.client as c:
            resp = c.post('/users/unlike/2121', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Unauthorized, can not delete like.", html)