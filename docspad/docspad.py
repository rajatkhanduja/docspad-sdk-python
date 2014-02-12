import json
import requests

class DocspadError(Exception):
    pass

class InvalidKeyError(DocspadError):
    def __init__(self, consumer_key):
        Exception.__init__(self, "Invalid key : " + consumer_key)

class UnexpectedResponseError(DocspadError):
    def __init__(self, code):
        Exception.__init__(self, "Received HTTP code : " + code)

class InvalidDocIdError(DocspadError):
    def __init__(self, doc_id):
        Exception.__init__(self, "Invalid docId : " + doc_id)

class DeletionError(DocspadError):
    pass

class DocNameNotSpecifiedError(DocspadError):
    pass


class FileStatus:
    PRESENT = 'PRESENT'
    DELETED = 'DELETED'

class ConversionStatus:
    QUEUED      = 'QUEUED'
    DOWNLOADING = 'DOWNLOADING'
    CONVERTING  = 'CONVERTING'
    COMPLETED   = 'COMPLETED'

class Status:
    def __init__(self, status_dict):
        self.status            = status_dict
        self.file_status       = status_dict['file_status']
        self.conversion_status = status_dict['conversion_status']

    def __repr__(self):
        return str(self.status)

class DocspadClient:

    _BASE_URL   = "http://apis.docspad.com"
    _VERSION    = "v1"
    _UPLOAD_PATH  = "/upload.php"
    _STATUS_PATH  = "/status.php"
    _SESSION_PATH = "/session.php"
    _DELETE_PATH  = "/delete.php"
    _VIEW_PATH    = "/view"

    def _get_url(self, path):
        return self._BASE_URL + "/" + self._VERSION + path

    def _handle_error(self, request_params, response):
        if response != 1:
            if 'error' in response:
                error_msg = response['error']['msg']

                if error_msg == 'API key being supplied is invalid':
                    raise InvalidKeyError(self.consumer_key)
                elif error_msg == 'Sorry docName must be specified':
                    raise DocNameNotSpecifiedError
                elif error_msg == 'Doc id being passed is invalid':
                    raise InvalidDocIdError(request_params['docId'])
                else:
                    raise DocspadError(response['error'])

    def __init__(self, consumer_key):
        self.consumer_key = consumer_key

    def _post(self, url, post_params, files = {}):
        if 'key' not in post_params:
            post_params['key'] = self.consumer_key

        if len(files) == 0:
            resp = requests.post(url, data=post_params)
        else:
            resp = requests.post(url, data=post_params, files=files)

        if resp.status_code != 200:
            raise UnexpectedResponseError(resp.status_code)

        returned_message = json.loads(resp.text)
        self._handle_error(post_params, returned_message)

        return returned_message

    def upload(self, path_to_file, is_url=False):
        upload_url = self._get_url(self._UPLOAD_PATH)
        data_parameter = {'doc':path_to_file}

        if is_url:
            returned_message = self._post(upload_url, data_parameter)
        else:
            returned_message = self._post(upload_url, data_parameter, files={'doc':open(path_to_file)})

        return DocspadDocument(self, returned_message['docId'])

    def get_status(self, doc_id):
        return Status(self._post(self._get_url(self._STATUS_PATH), {'docId':doc_id}))

    def get_new_session(self, doc_id):
        returned_message = self._post(self._get_url(self._SESSION_PATH), {'docId':doc_id})
        return returned_message['sessionId']

    def delete(self, id, delete_doc=True):
        if delete_doc:
            returned_message = self._post(self._get_url(self._DELETE_PATH), {'docId':id})
        else:
            returned_message = self._post(self._get_url(self._DELETE_PATH), {'sessionId':id})
        if returned_message != '1':
            raise DeletionError(returned_message)

    def view_url(self,session_id):
        return self._get_url(self._VIEW_PATH) + "/" + session_id + "/index.html"

class DocspadDocument:

    def __init__(self, docspadClient, doc_id):
        self.docspadClient = docspadClient
        self.doc_id = doc_id

    def status(self):
        return self.docspadClient.get_status(self.doc_id)

    def get_new_session(self):
        return self.docspadClient.get_new_session(self.doc_id)

    def delete_session(self, session_id):
        self.docspadClient.delete(session_id, False)

    def delete(self):
        self.docspadClient.delete_doc(self.doc_id)

    def get_view_url(self, session_id=None):
        if session_id == None:
            session_id = self.get_new_session()
        return self.docspadClient.view_url(session_id)