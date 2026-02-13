from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

try:
    from django.core.files.storage import get_storage_class as _get_storage_class

    def _get_storage_instance(path_or_alias):
        storage_class = _get_storage_class(path_or_alias)
        return storage_class()

except ImportError:  # Django 5.x+: get_storage_class removed
    from django.core.files.storage import storages, InvalidStorageError
    from django.utils.module_loading import import_string

    def _get_storage_instance(path_or_alias):
        try:
            return storages[path_or_alias]
        except InvalidStorageError:
            pass
        return import_string(path_or_alias)()


class StaticStorage(S3Boto3Storage):
    location = getattr(settings, 'AWS_STATIC_LOCATION', 'static')
    file_overwrite = True
    default_acl = 'public-read'


class PublicMediaStorage(S3Boto3Storage):
    location = getattr(settings, 'AWS_PUBLIC_MEDIA_LOCATION', None)
    file_overwrite = True
    default_acl = 'public-read'


class PrivateMediaStorage(S3Boto3Storage):
    location = getattr(settings, 'AWS_PRIVATE_MEDIA_LOCATION', None)
    default_acl = 'private'
    file_overwrite = True
    custom_domain = False


class PrivateSequencingStorage(S3Boto3Storage):
    location = getattr(settings, 'AWS_PRIVATE_SEQUENCING_LOCATION', None)
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False


class PrivateBackupStorage(S3Boto3Storage):
    location = getattr(settings, 'AWS_PRIVATE_BACKUP_LOCATION', None)
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False


# https://stackoverflow.com/questions/59437637/django-use-private-s3-storage-only-in-production-environment
def select_private_media_storage():
    return _get_storage_instance(settings.PRIVATE_FILE_STORAGE)


def select_private_sequencing_storage():
    return _get_storage_instance(settings.PRIVATE_SEQUENCING_FILE_STORAGE)


def select_public_media_storage():
    return _get_storage_instance(settings.DEFAULT_FILE_STORAGE)
