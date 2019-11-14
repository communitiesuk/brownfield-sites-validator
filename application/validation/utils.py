import codecs
import collections
import csv
import os
import tempfile

from cchardet import UniversalDetector
from application.validation.schema import brownfield_site_schema


class FileTypeException(Exception):

    def __init__(self, message):
        self.message = message


class BrownfieldStandard:

    @staticmethod
    def v1_standard_headers():
        return ['OrganisationURI',
                'OrganisationLabel',
                'SiteReference',
                'PreviouslyPartOf',
                'SiteNameAddress',
                'SiteplanURL',
                'CoordinateReferenceSystem',
                'GeoX',
                'GeoY',
                'Hectares',
                'OwnershipStatus',
                'Deliverable',
                'PlanningStatus',
                'PermissionType',
                'PermissionDate',
                'PlanningHistory',
                'ProposedForPIP',
                'MinNetDwellings',
                'DevelopmentDescription',
                'NonHousingDevelopment',
                'Part2',
                'NetDwellingsRangeFrom',
                'NetDwellingsRangeTo',
                'HazardousSubstances',
                'SiteInformation',
                'Notes',
                'FirstAddedDate',
                'LastUpdatedDate']

    @staticmethod
    def v2_standard_headers():
        return [item['name'] for item in brownfield_site_schema['fields']]

    @staticmethod
    def headers_deprecated():
        return list(set(BrownfieldStandard.v1_standard_headers()) - set(BrownfieldStandard.v2_standard_headers()))


def try_convert_to_csv(filename):
    import subprocess
    try:
        if filename.endswith('.xls'):
            with open(f'{filename}.csv', 'w') as out:
                subprocess.check_call(['in2csv', filename], stdout=out)
            return f'{filename}.csv', filename.split('.')[-1]
        elif filename.endswith('.xlsm'):
            with open(f'{filename}.csv', 'w') as out:
                subprocess.check_call(['xlsx2csv', filename], stdout=out)
            return f'{filename}.csv', 'xlsm'
    except Exception as e:
        msg = f"We could not convert {filename.split('/')[-1]} into csv"
        raise FileTypeException(msg)


def extract_data(upload_data, filename):
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = f'{temp_dir}/data'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        file = os.path.join(output_dir, filename)
        upload_data.save(file)
        if not _looks_like_csv(file):
            file, original_file_type = try_convert_to_csv(file)
        else:
            original_file_type = 'csv'
        data = csv_to_dict(file)
        data['file_type'] = original_file_type
        return data


def csv_to_dict(csv_file):
    rows_to_check = []
    original_rows = []
    encoding = detect_encoding(csv_file)
    planning_authority = None
    with codecs.open(csv_file, encoding=encoding['encoding']) as f:
        reader = csv.DictReader(f)
        additional_headers = list(set(reader.fieldnames) - set(BrownfieldStandard.v2_standard_headers()))
        headers_missing = list(set(BrownfieldStandard.v2_standard_headers()) - set(reader.fieldnames))
        for row in reader:
            to_check = collections.OrderedDict()
            # TODO get planning authority name from opendatacommunities
            if planning_authority is None:
                planning_authority = row.get('OrganisationLabel', 'Unknown')
            for column in BrownfieldStandard.v2_standard_headers():
                value = row.get(column, None)
                if value is not None:
                    to_check[column] = row.get(column)
            rows_to_check.append(to_check)
            original_rows.append(row)
    return {'rows_to_check': rows_to_check,
            'original_rows': original_rows,
            'headers_found': reader.fieldnames,
            'additional_headers': additional_headers,
            'headers_missing': headers_missing,
            'planning_authority': planning_authority}


def detect_encoding(file):
    detector = UniversalDetector()
    detector.reset()
    with open(file, 'rb') as f:
        for row in f:
            detector.feed(row)
            if detector.done:
                break
    detector.close()
    return detector.result


def get_markdown_for_field(field_name):
    from pathlib import Path
    current_directory = Path(__file__).parent.resolve()
    markdown_file = Path(current_directory, 'markdown', f'{field_name}.md')
    with open(markdown_file) as f:
        content = f.read()
    return content


def _looks_like_csv(file):
    try:
        with open(file) as f:
            content = f.read()
            csv.Sniffer().sniff(content)
            return True
    except Exception as e:
        return False