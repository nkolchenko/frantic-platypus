"""
    Interpreter: Python 3.6

    The below code extends the SimpleHTTPRequestHandler class from the http.server module.
    Additionally I've been using:
        https://docs.python.org/3.6/library/http.server.html
        https://gist.github.com/fabiand/5628006
        https://stackoverflow.com/questions/25316046/parsing-get-request-data-with-from-simplehttpserver
        https://docs.python.org/3/library/urllib.parse.html
        https://www.w3schools.com/python/ref_string_split.asp :-)
"""
import http.server
import socketserver
from urllib.parse import urlparse
from http import HTTPStatus
from datetime import date, datetime
import pymysql
import pymysql.cursors
import json

def open_kiwi_db():
    # Connect to the database
    connection = pymysql.connect(host='localhost',
                                 user='kiwi_user',
                                 password='pss73549189w',
                                 db='kiwi_task',
                                 charset='utf8',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection


def close_kiwi_db(connection):
    print("close_kiwi_db:   closing connection")
    connection.close()
    print("close_kiwi_db:   connection CLOSED")


def modify_data(username,birth_date_str, connection):
    with connection.cursor() as cursor:
        print("modify_data:   entered")
        sql = "INSERT INTO `user_data` (`username`, `birth_date_str`) VALUES (%s,%s) ON DUPLICATE KEY UPDATE birth_date_str=%s"
        cursor.execute(sql, (username, birth_date_str, birth_date_str))
        print("modify_data:   "+str((sql, (username, birth_date_str, birth_date_str))))
    connection.commit()


def select_data(username, connection):
    with connection.cursor() as cursor:
        # Read a single record
        sql = "SELECT `birth_date_str` FROM `user_data` WHERE `username` =%s"
        cursor.execute(sql, (username))
        birth_date_dict = cursor.fetchone()
        # Example: birth_date_dict= {'birth_date_str': '1984-03-17'}   it's a dictionary
        birth_date_str = birth_date_dict['birth_date_str']

        print("select_data:   birth_date_str= "+str(birth_date_str))

    return birth_date_str


def srv_run():
    port = 8888


    handler = ExtendedHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    print("serving at port", port)
    httpd.serve_forever()


def calculate_dates(birth_date, curr_date):

    # Feb29th workaround. We can't let anyone to be upset with the fact that he/she shall wait for more than 365days
    # for the next Birthday! :-D  Replace Feb 29th with Mar 1st for days_untill_bday calculation.

    if birth_date.month == 2 and birth_date.day == 29:
        birth_date_adjusted = birth_date.replace(month=0o3, day=0o1)

        print("calculate_dates:   leap year conversion " + str(birth_date_adjusted))
        birth_date = birth_date_adjusted

    this_year_bdate = datetime(curr_date.year, birth_date.month, birth_date.day)
    print("calculate_dates:   this year b-day: "+ str(this_year_bdate))
    next_year_bdate = datetime(curr_date.year+1, birth_date.month, birth_date.day)
    print("calculate_dates:   next year b-day: "+ str(next_year_bdate ))

    if curr_date > this_year_bdate:
        days_untill_bday = (next_year_bdate - curr_date).days
    else:
        days_untill_bday = (this_year_bdate - curr_date).days
    print("calculate_dates:   days_untill_bday: " + str(days_untill_bday))
    return days_untill_bday


def get_days(birth_date_str):
    curr_date_str = datetime.strftime(date.today(), '%Y-%m-%d')
    curr_date = datetime.strptime(curr_date_str, '%Y-%m-%d')
    print("get_days:   curr_date: " + str(curr_date))

    birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
    print("get_days:   birth_date: " + str(birth_date))

    days_untill_bday = calculate_dates(birth_date, curr_date)

    """
            A. if username's birthday is in N days:
                { "message": "Hello, <username>! Your birthday is in N day(s)" }
            B. if username's birthday is today:
                { "message": "Hello, <username>! Happy birthday!" }
    """

    return days_untill_bday


def construct_body(username, days_untill_bday):

    if days_untill_bday > 0:
        message = "Hello, "+str(username)+"! Your birthday is in " + str(days_untill_bday) + " day(s)"
    else:
        message = "Hello, "+str(username)+"! Happy birthday!"
    print("construct_body:   message: "+str(message))
    return message


class ExtendedHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    from urllib.parse import urlparse
    def send_reply(self, message):
        #message = name
        print("send_reply:   body: "+str(message))

        self.send_response(HTTPStatus.OK)
        #self.send_response(201, " DONE ")

        #self.send_header("Content-type", "html/text")
        #self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        #self.end_headers()
        #self.send_response(201, " DONE ")

        #body = None


        body = message.encode('UTF-8', 'replace')
        self.send_header("Content-type", "text/html")
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


    def do_PUT(self):
        """
        Saves/updates given user's name and birthdate to database:
        Request: PUT /hello/<username> {"dateOfBirth": "YYYY-MM-DD"}
        curl -v -X PUT -H "Content-Type: application/json" -d '{"dateOfBirth": "1999-03-03"}' localhost:8889/hello/sman

        Response: 204 No Content
        Rules:
            - username must contain only letters;
            - date must be before current date
        """
        self.send_response(204, "No Content")
        self.end_headers()

        print("Headers: ")
        print(self.headers)
        print("Path: "+str(self.path))

        path_split = self.path.split("/", 2)
        username = path_split[-1]
        print("do_PUT:   username: " + str(path_split[-1]))  # nikolay/uuuuer

        length = int(self.headers["Content-Length"])
#        path = self.translate_path(self.path)
#        with open(path, "wb") as dst:
#            dst.write(self.rfile.read(length))

        ''' 
        I assume that the following structure is sent as a payload: {"dateOfBirth": "1999-03-03"} (JSON, double quotes)
        '''
        bytes_payload = self.rfile.read(length)
        payload_str = bytes_payload.decode("utf-8")  # that's a string: {"dateOfBirth": "1999-03-03"}
        payload_list = payload_str.split("\"")        # that's a list: ['{', 'dateOfBirth', ': ', '1999-03-03', '}']
        birth_date_str = payload_list[3]                     # that's a 1999-03-03


        print("do_PUT:   birth_date_str: "+str(birth_date_str))

        print("do_PUT:   Let's open db_conn")
        connection = open_kiwi_db()
        print("do_PUT:   opened!")
        modify_data(username, birth_date_str, connection)
        print("do_PUT:   new data is sent to db!")
        close_kiwi_db(connection)
        print("do_PUT:   DONE! \n")


    def do_GET(self):
        """
        Returns hello birthday message for given user
            Request: GET /hello/<username>
            Response: 200 OK
        """
        print("do_GET:   got: " + str(self.path))

        path_split = self.path.split("/", 2)
        print("do_GET:   path_split: "+str(path_split))              #  ['', 'hello', 'nikolay/uuuuer']
        username = path_split[-1]
        print("do_GET:   username: " + str(path_split[-1]))  # nikolay/uuuuer

        #bits = urlparse(self.path)
        #print(name, self.path, self.command, self.request_version, bits.scheme, bits.netloc,
        #                bits.path, bits.params, bits.query, bits.fragment,
        #                bits.username, bits.password, bits.hostname, bits.port)

        # TODO: get_data_from_mysql(username)                       -->  get  birth_date_str  for username

        print("do_GET:   Let's open db_conn")
        connection = open_kiwi_db()
        print("do_GET:   opened!")
        birth_date_str = select_data(username, connection)
        close_kiwi_db(connection)

        days_untill_bday = get_days(birth_date_str)
        message = construct_body(username, days_untill_bday)
        #message = username

        #self.send_response(HTTPStatus.OK)
        self.send_reply(message)
#        self.send_header("Content-type", ctype)
        print("do_GET:   DONE! \n")


if __name__ == '__main__':

    print("Let's start web-server\n")
    srv_run()
