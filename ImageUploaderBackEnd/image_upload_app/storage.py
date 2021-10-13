import re

from storages.backends.s3boto3 import S3Boto3Storage
from django.utils.deconstruct import deconstructible
from django.utils.functional import keep_lazy_text
from ImageUploaderBackEnd import settings


@keep_lazy_text
def get_valid_filename(s):
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w@.]', '', s)


@deconstructible
class S3StorageIU(S3Boto3Storage):
    base_url = settings.AWS_URL

    def get_valid_name(self, name):
        return get_valid_filename(name)
