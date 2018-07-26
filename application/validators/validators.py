"""
    Sketch of a validation approach for csv files.
    Heavily influenced by (that is to say, ripped off from https://github.com/di/vladiate)
"""

import csv
import json
import logging
import requests

from io import StringIO
from collections import defaultdict
from enum import Enum
from requests.exceptions import InvalidSchema, HTTPError, MissingSchema

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Error(Enum):
    INVALID_URL = 'An invalid URL was found in the file'
    INVALID_DATE = 'Date format should be YYYY-MM-DD'
    NO_LINE_BREAK = 'No line breaks allowed'
    REQUIRED_FIELD = 'Required data is missing'
    INVALID_FLOAT = 'This field must contain a floating point number'
    INVALID_CSV_HEADERS = 'This file does not contain the expected headers'

    def to_dict(self):
        return {'type': self.name, 'message': self.value}


class Warning(Enum):
    HTTP_WARNING = 'There was a problem fetching data from a URL in the file'
    DATE_WARNING = 'The date is in the future. Please check'
    CONTENT_TYPE_WARNING = 'Set Content-Type to test/csv;charset-utf8'
    FILE_ENCODING_WARNING = 'File should be encoded as utf-8'

    def to_dict(self):
        return {'type': self.name, 'message': self.value}



class StringInput():

    ''' Read a file from a string '''

    def __init__(self, string_input=None, string_io=None):
        self.string_io = string_io if string_io else StringIO(string_input)

    def open(self):
        return self.string_io


class BaseFieldValidator:

    def __init__(self, allow_empty=False):
        self.allow_empty = allow_empty

    def validate(self, field, row):
        raise NotImplementedError


class URLValidator(BaseFieldValidator):

    ''' Field must be a valid url and reachable '''

    def __init__(self, **kwargs):
        super(URLValidator, self).__init__(**kwargs)
        self.checked = set([])

    def validate(self, data, row={}):
        errors = []
        warnings = []
        if (data or not self.allow_empty) and data not in self.checked:
            try:
                resp = requests.head(data)
                resp.raise_for_status()
                self.checked.add(data)
            except (InvalidSchema, MissingSchema) as e:
                errors.append({'data': data, 'error': Error.INVALID_URL.to_dict(), 'message' : str(e)})
                logger.info('Found error with', data)
            except HTTPError as e:
                warnings.append({'data': data, 'warning': Warning.HTTP_WARNING.to_dict(), 'message' : str(e)})
                logger.info('Found warning with', data)

        return errors, warnings


class StringNoLineBreaksValidator(BaseFieldValidator):

    ''' Field cannot contain line breaks '''

    def __init__(self, **kwargs):
        super(StringNoLineBreaksValidator, self).__init__(**kwargs)

    def validate(self, data, row={}):
        errors = []
        warnings = []
        if (data or not self.allow_empty) and ('\r\n' in data or '\n' in data):
            errors.append({'data': data, 'error': Error.NO_LINE_BREAK.to_dict()})
            logger.info('Found error with', data)
        return errors, warnings


class ISO8601DateValidator(BaseFieldValidator):

    ''' Field must be iso-8601 formatted date string '''

    def __init__(self, **kwargs):
        super(ISO8601DateValidator, self).__init__(**kwargs)

    def validate(self, data, row={}):
        import datetime
        errors = []
        warnings = []
        if data or not self.allow_empty:
            try:
                datetime.datetime.strptime(data, '%Y-%m-%d')
            except ValueError as e:
                errors.append({'data': data, 'error': Error.INVALID_DATE.to_dict()})
                logger.info('Found error with', data)

        return errors, warnings


class NotEmptyValidator(BaseFieldValidator):

    ''' Field cannot be empty '''

    def __init__(self, **kwargs):
        super(NotEmptyValidator, self).__init__(**kwargs)

    def validate(self, data, row={}):
        errors = []
        warnings = []
        if data.strip() == '':
            errors.append({'data': data, 'error': Error.REQUIRED_FIELD.to_dict()})
            logger.info('Found error with', data)
        return errors, warnings


class FloatValidator(BaseFieldValidator):

    def __init__(self, **kwargs):
        super(FloatValidator, self).__init__(**kwargs)

    def validate(self, data, row={}):
        errors = []
        warnings = []
        try:
            if data or not self.allow_empty:
                float(data)
        except ValueError as e:
            errors.append({'data': data, 'error': Error.INVALID_FLOAT.to_dict()})
            logger.info('Found error with', data)
        return errors, warnings


class AnythingValidator(BaseFieldValidator):
    ''' Field needs to be present but can be pretty much any content '''

    def validate(self, field, row={}):
        pass


class CrossFieldValidator(BaseFieldValidator):

    ''' Checks field against another field in row '''

    def __init__(self, validate_against_fields=[], **kwargs):
        super(CrossFieldValidator, self).__init__(**kwargs)
        self.validate_against_fields = validate_against_fields

    def validate(self, field, row):
        # because we have access to entire row then we can validate against other fields
        pass


class RegisterValidator:

    def __init__(self, source, file_warnings, line_count, validators={}, delimiter=None):

        self.source = source
        self.file_warnings = file_warnings
        self.file_errors = []
        self.line_count = line_count
        self.errors = defaultdict(lambda: defaultdict(list))
        self.warnings = defaultdict(lambda: defaultdict(list))
        self.missing = []
        self.unknown = []
        self.validators = validators or getattr(self, 'validators', {})
        self.delimiter = delimiter or getattr(self, 'delimiter', ',')
        self.rows_analysed = 0
        self.report = {}

    def to_dict(self):
        return {'errors': self.errors,
                'warnings': self.warnings,
                'file_errors': self.file_errors,
                'file_warnings': self.file_warnings,
                'missing': list(self.missing),
                'unknown': list(self.unknown),
                'line_count': self.line_count,
                'rows_analysed': self.rows_analysed,
                'report': self.report}

    def validate(self):

        reader = csv.DictReader(self.source.open(), delimiter=self.delimiter)
        self.missing = set(self.validators) - set(reader.fieldnames)
        self.unknown = set(reader.fieldnames) - set(self.validators)

        # if this happens, then file headers are completely broken and not point
        # carrying on
        if self.missing == set(self.validators):
            self.file_errors = {'data': 'file', 'error': Error.INVALID_CSV_HEADERS.to_dict()}
            self.unknown = set(reader.fieldnames)
            return self

        for line, row in enumerate(reader):
            self.rows_analysed += 1
            for field_name, field in row.items():
                if field_name in self.validators:
                    for validator in self.validators[field_name]:
                        errors, warnings = validator.validate(field, row=row)
                        if errors:
                            self.errors[field_name][line].extend(errors)
                        if warnings:
                            self.warnings[field_name][line].extend(warnings)

        self._gather_results()

        return self

    def _gather_results(self):

        for field, errors in self.errors.items():
            error_type_count = {}
            for line_number, errs in errors.items():
                for err in errs:
                    err_type = err['error']['type']
                    if err_type not in error_type_count:
                        error_type_count[err_type] = 1
                    else:
                        error_type_count[err_type] = error_type_count[err_type] + 1
            self.report[field] = {'errors' :  error_type_count}

        for field, warnings in self.warnings.items():
            warning_type_count = {}
            for line_number, warns in warnings.items():
                for warn in warns:
                    warn_type = warn['warning']['type']
                    if warn_type not in warning_type_count:
                        warning_type_count[warn_type] = 1
                    else:
                        warning_type_count[warn_type] = warning_type_count[warn_type] + 1
            self.report[field] = {'warnings': warning_type_count}


class BrownfieldSiteValidator(RegisterValidator):

    valid_coordinate_reference_system = ['WGS84', 'OSGB36', 'ETRS89']
    ownership_status_pattern = r'(?i)(owned by a public authority|not owned by a public authority|unknown ownership|mixed ownership)'
    planning_status_pattern = r'(?i)(permissioned|not permissioned|pending decision)'
    permission_type_pattern = r'(?i)(full planning permission|outline planning permission|reserved matters approval|permission in principle|technical details consent|planning permission granted under an order|other)'

    validators = {
        'OrganisationURI' : [
            NotEmptyValidator(),
            URLValidator()
        ],
        'OrganisationLabel' : [
            NotEmptyValidator(),
            StringNoLineBreaksValidator()
        ],
        'SiteReference': [
            NotEmptyValidator(),
            StringNoLineBreaksValidator()
        ],
        'PreviouslyPartOf': [
            StringNoLineBreaksValidator(allow_empty=True)
        ],
        'SiteNameAddress': [
            NotEmptyValidator(),
            StringNoLineBreaksValidator()
        ],
        'SiteplanURL': [
            NotEmptyValidator(),
            URLValidator()
        ],
        'CoordinateReferenceSystem': [
            NotEmptyValidator(),
        ],
        'GeoX': [
            NotEmptyValidator(),
            FloatValidator()
        ],
        'GeoY': [
            NotEmptyValidator(),
            FloatValidator()
        ],
        'Hectares': [
            NotEmptyValidator(),
            FloatValidator()
        ],
        'OwnershipStatus': [
            NotEmptyValidator()
        ],
        'Deliverable': [],
        'PlanningStatus': [
            NotEmptyValidator()
        ],
        'PermissionType': [],
        'PermissionDate': [
            ISO8601DateValidator(allow_empty=True)
        ],
        'PlanningHistory': [
            URLValidator(allow_empty=True)
        ],
        'ProposedForPIP': [],
        'MinNetDwellings': [
            NotEmptyValidator()
        ],
        'DevelopmentDescription': [],
        'NonHousingDevelopment': [],
        'Part2': [],
        'NetDwellingsRangeFrom': [],
        'NetDwellingsRangeTo': [],
        'HazardousSubstances': [],
        'SiteInformation': [
            URLValidator(allow_empty=True)
        ],
        'Notes': [],
        'FirstAddedDate': [
            ISO8601DateValidator(),
        ],
        'LastUpdatedDate': [
            ISO8601DateValidator()
        ]
    }