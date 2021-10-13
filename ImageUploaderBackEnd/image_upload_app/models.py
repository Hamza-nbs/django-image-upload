from django.db import models
from .storage import S3StorageIU


class ImageUpload(models.Model):
    pass


class AcumaticaUpload(models.Model):
    inventory_id = models.CharField(max_length=40)
    serial_number = models.CharField(max_length=40, blank=True, null=True)
    image_upload = models.OneToOneField(ImageUpload,
                                        related_name='acumatica',
                                        on_delete=models.CASCADE)
    original_large = models.ImageField(upload_to='acumatica/original',
                                       storage=S3StorageIU(),
                                       null=False, blank=False)
    original_small = models.ImageField(upload_to='acumatica/original',
                                       storage=S3StorageIU(),
                                       null=True, blank=True)
    large = models.ImageField(upload_to='acumatica/large',
                              storage=S3StorageIU(),
                              null=False, blank=False)
    search = models.ImageField(upload_to='acumatica/search',
                               storage=S3StorageIU(),
                               null=False, blank=False)
    icon = models.ImageField(upload_to='acumatica/icon',
                             storage=S3StorageIU(),
                             null=False, blank=False)


class WebUpload(models.Model):
    image_upload = models.ForeignKey(ImageUpload,
                                     related_name='web',
                                     on_delete=models.CASCADE)

    index = models.PositiveSmallIntegerField()

    original = models.ImageField(upload_to='web/original',
                                 storage=S3StorageIU(),
                                 null=False, blank=False)
    product = models.ImageField(upload_to='web/product',
                                storage=S3StorageIU(),
                                null=False, blank=False)
    product_retina = models.ImageField(upload_to='web/product',
                                       storage=S3StorageIU(),
                                       null=False, blank=False)
    grid = models.ImageField(upload_to='web/grid',
                             storage=S3StorageIU(),
                             null=False, blank=False)
    grid_retina = models.ImageField(upload_to='web/grid',
                                    storage=S3StorageIU(),
                                    null=False, blank=False)
    altview = models.ImageField(upload_to='web/altviews',
                                storage=S3StorageIU(),
                                null=False, blank=False)
    altview_retina = models.ImageField(upload_to='web/altviews',
                                       storage=S3StorageIU(),
                                       null=False, blank=False)

    class Meta:
        unique_together = ('image_upload', 'original')
