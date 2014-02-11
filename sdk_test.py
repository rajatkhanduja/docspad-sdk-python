from time import sleep
import docspad

try:
    client = docspad.DocspadClient('cf1QlwiylaRz7PaG')
    doc = client.upload('/home/rajat/Desktop/APIDocumentationv1.pdf')
    print doc.doc_id
    status = doc.status()   # Can also use `client.get_status(doc.doc_id)`

    while status.conversion_status != docspad.ConversionStatus.COMPLETED:
        print status
        sleep(2)
        status = doc.status()

    session_id = doc.get_new_session()     # Can also use `client.get_new_session(doc.doc_id)`
    doc.delete_session(session_id)
    doc.delete()
    print doc.status()
except docspad.DocspadError  as e:
    print e