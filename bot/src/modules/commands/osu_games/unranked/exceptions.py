


class CancelSubmit(Exception):
    def __init__(self, incorrections_list=None):
        self.incorrections_list = incorrections_list

class CancelTryFinish(Exception):
    def __init__(self, list=None, forward_list_back=None, finished=None):
        self.list = list
        self.forward_list_back = forward_list_back
        self.finished = finished

class StopTransaction(Exception):
    def __init__(self, answer=None, edit=None, send=None):
        self.answer = answer
        self.edit = edit
        self.send = send

class AuthException(Exception):
    def __init__(self, answer=None, edit=None, send=None):
        self.answer = answer
        self.edit = edit
        self.send = send