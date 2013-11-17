from urlparse import urlparse
import os
import urllib2
from scratchtobat import sb2, common
import re
import hashlib

HTTP_PROJECT_API = "http://scratch.mit.edu/internalapi/project/{}/get/"
HTTP_ASSET_API = "http://scratch.mit.edu/internalapi/asset/{}/get/"
HTTP_PROJECT_URL_PREFIX = "http://scratch.mit.edu/projects/"
HTTP_PROJECT_URL_PATTERN = HTTP_PROJECT_URL_PREFIX + r'\d+/?'


def download_project(project_url, target_dir):
    if not re.match(HTTP_PROJECT_URL_PATTERN, project_url):
        raise common.ScratchtobatError("Project URL must be matching '{}'. Given: {}".format(
            HTTP_PROJECT_URL_PREFIX + '<project id>', project_url))

    def data_of_request_response(url):
        common.log.info("Requesting web api url: {}".format(url))
        return urllib2.urlopen(url).read()

    def request_project_data(project_id):
        try:
            return data_of_request_response(project_json_request_url(project_id))
        except urllib2.HTTPError as e:
            raise common.ScratchtobatError(e)

    def request_resource_data(md5_file_name):
        request_url = project_resource_request_url(md5_file_name)
        try:
            response_data = data_of_request_response(request_url)
            verify_hash = hashlib.md5(response_data).hexdigest()
            assert verify_hash == os.path.splitext(md5_file_name)[0], "MD5 hash of response data not matching"
            return response_data
        except urllib2.HTTPError as e:
            raise common.ScratchtobatError(e)

    def project_json_request_url(project_id):
        return HTTP_PROJECT_API.format(project_id)

    def project_resource_request_url(md5_file_name):
        return HTTP_ASSET_API.format(md5_file_name)

    def project_id_from_url(project_url):
        normalized_url = project_url.strip("/")
        project_id = os.path.basename(urlparse(normalized_url).path)
        return project_id

    def write_to(data, file_path):
        with open(file_path, "wb") as fp:
            fp.write(data)

    def project_code_path(target_dir):
        return os.path.join(target_dir, sb2.Project.SCRATCH_PROJECT_CODE_FILE)

    project_id = project_id_from_url(project_url)
    project_file_path = project_code_path(target_dir)
    write_to(request_project_data(project_id), project_file_path)

    project_code = sb2.ProjectCode(project_file_path)
    for md5_file_name in project_code.md5_file_names_of_referenced_resources():
        resource_file_path = os.path.join(target_dir, md5_file_name)
        write_to(request_resource_data(md5_file_name), resource_file_path)
