class NCMException(Exception):
    pass

class NCMFileValidationException(NCMException):
    pass

class NCMDecryptionException(NCMException):
    pass

class NCMExportException(NCMException):
    pass
