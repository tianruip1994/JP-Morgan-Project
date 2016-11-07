import os
import server
import unittest
import tempfile

class ServerTestCase(unittest.TestCase):

    def setUp(self):
     with server.app.app_context():
        self.db_fd, server.app.config['DATABASE'] = tempfile.mkstemp()
        server.app.config['TESTING'] = True
        self.app = server.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(server.app.config['DATABASE'])

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/signout', follow_redirects=True)

    # test need to start with "test_"
    def test_main_page(self):
        rv = self.app.get('/')
        assert b'Welcome! This is main page' in rv.data

    def test_register(self):
        rv=self.app.post('/register',data=dict(username='test',password='12345'), follow_redirects=True)
        assert 'The username you typed is already used' in rv.data
        rv=self.app.post('/register',data=dict(username='test_register',password='12345'), follow_redirects=True)
        assert 'successfully registered' in rv.data
        rv=self.app.post('/register',data=dict(username='test_abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz',
                                                password='12345'), follow_redirects=True)
        assert 'successfully registered' in rv.data

    def test_login_logout(self):
        rv = self.login('test', '12345')
        assert 'Welcome test!' in rv.data
        rv = self.logout()
        assert 'Welcome! This is main page' in rv.data
        rv = self.login('test','123')
        assert 'Oops! We cannot find this combination' in rv.data

    def test_submit_order(self):
        self.login('test', '12345')
        rv = self.app.post('/submitOrder', data=dict(volume=5000), follow_redirects=True)
        assert '5000' in rv.data
        #test nonpositive integer
        rv = self.app.post('/submitOrder', data=dict(volume='abc'), follow_redirects=True)
        assert 'positive integer' in rv.data
        rv = self.app.post('/submitOrder', data=dict(volume='-1'), follow_redirects=True)
        assert 'positive integer' in rv.data
        rv = self.app.post('/submitOrder', data=dict(volume='0'), follow_redirects=True)
        assert 'positive integer' in rv.data
        rv = self.app.post('/submitOrder', data=dict(volume='2147483648'), follow_redirects=True)
        assert 'positive integer' in rv.data

if __name__ == '__main__':
    unittest.main()