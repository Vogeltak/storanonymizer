from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from storanonymizer import app

server = HTTPServer(WSGIContainer(app))
server.listen(5000)
IOLoop.instance().start()