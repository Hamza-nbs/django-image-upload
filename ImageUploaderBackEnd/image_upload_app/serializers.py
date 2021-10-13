from django.utils.deconstruct import deconstructible

from rest_framework.serializers import ValidationError, ModelSerializer, \
    CharField, ImageField

from .models import ImageUpload, AcumaticaUpload, WebUpload
from .utils import modify_n_get, get_name_extension, push_to_acumatica

from PIL import Image


@deconstructible
class ImageSizeValidator:
    def __init__(self, min_width, min_height, name):
        self.min_width = min_width
        self.min_height = min_height
        self.name = name

    def __call__(self, value, *args, **kwargs):
        image_value = Image.open(value)
        width, height = image_value.size
        if width < self.min_width and height < self.min_height:
            raise ValidationError('Size of %s Image should be at least with %s width or %s length' %
                                  (self.name, self.min_width, self.min_height))
        return value


class WebUploadSerializer(ModelSerializer):
    class Meta:
        model = WebUpload
        fields = ('index',
                  'original',
                  'product',
                  'product_retina',
                  'grid',
                  'grid_retina',
                  'altview',
                  'altview_retina')


class AcumaticaUploadSerializer(ModelSerializer):
    class Meta:
        model = AcumaticaUpload
        fields = ('inventory_id',
                  'serial_number',
                  'original_large',
                  'original_small',
                  'large',
                  'search',
                  'icon')


def web_view_image_field(index):
    return ImageField(max_length=None,
                      allow_empty_file=True,
                      required=False,
                      write_only=True,
                      validators=[ImageSizeValidator(1440, 1440, 'Web View %d' % index)])


class ImageUploadSerializer(ModelSerializer):
    inventory_id = CharField(required=False,
                             write_only=True,
                             max_length=40)
    serial_number = CharField(required=False,
                              write_only=True,
                              max_length=40)
    large_image = ImageField(required=False,
                             write_only=True,
                             validators=[ImageSizeValidator(1024, 768, 'Large')])
    small_image = ImageField(required=False, write_only=True,
                             validators=[ImageSizeValidator(100, 75, 'Small')])
    web_image_1 = web_view_image_field(1)
    web_image_2 = web_view_image_field(2)
    web_image_3 = web_view_image_field(3)
    web_image_4 = web_view_image_field(4)
    web_image_5 = web_view_image_field(5)

    web = WebUploadSerializer(many=True, read_only=True)
    acumatica = AcumaticaUploadSerializer(read_only=True)

    class Meta:
        model = ImageUpload
        fields = ('inventory_id',
                  'serial_number',
                  'large_image',
                  'small_image',
                  'web_image_1',
                  'web_image_2',
                  'web_image_3',
                  'web_image_4',
                  'web_image_5',
                  'acumatica',
                  'web')

    def validate(self, data):
        s = 's' if 'large_image' in data and 'small_image' in data else ''
        web_images = [f'web_image_{i}' for i in range(1, 6)]
        web_images_data = [data[image] for image in web_images if image in data]
        if ('large_image' in data or 'small_image' in data) and 'inventory_id' not in data:
            raise ValidationError("To upload acumatica image%s inventory_id should be provided" % s)
        elif all(key not in data for key in ('large_image', 'small_image', *web_images)):
            raise ValidationError("Either large_image and\\or small_image or web_images should be provided")
        elif len(web_images_data) != len(set({item.name for item in web_images_data if item})):
            raise ValidationError("Contains images with the same name.")
        return data

    @staticmethod
    def create_acumatica(image_upload, acumatica_data):
        original_large = acumatica_data.get('large_image', None)
        original_small = acumatica_data.get('small_image', None)
        small_source = original_small if original_small else original_large
        inventory_id = acumatica_data.get('inventory_id')
        serial_number = acumatica_data.get('serial_number', None)
        name = inventory_id
        if serial_number:
            name += '-' + serial_number
        if original_large:
            original_large.name = name + get_name_extension(original_large.name)
        if original_small:
            original_small.name = name + '-small' + get_name_extension(original_small.name)
        args = {'image_upload': image_upload,
                'inventory_id': inventory_id,
                'serial_number': serial_number,
                'original_large': original_large,
                'original_small': original_small,
                'large': modify_n_get(original_large, name, 1024, 768, 'large'),
                'search': modify_n_get(small_source, name, 100, 75, 'search'),
                'icon': modify_n_get(small_source, name, 53, 40, 'icon')}
        AcumaticaUpload.objects.create(**args)

    @staticmethod
    def create_web(image_upload, web_image, index):
        args = {'index': index,
                'image_upload': image_upload,
                'original': web_image,
                'product': modify_n_get(web_image, None, 720, 720, 'product'),
                'product_retina': modify_n_get(web_image, None, 1440, 1440, 'product@2x'),
                'grid': modify_n_get(web_image, None, 375, 375, 'grid'),
                'grid_retina': modify_n_get(web_image, None, 750, 750, 'grid@2x'),
                'altview': modify_n_get(web_image, None, 58, 58, 'altview'),
                'altview_retina': modify_n_get(web_image, None, 116, 116, 'altview@2x')}
        WebUpload.objects.create(**args)

    def create(self, validated_data):
        image_upload = ImageUpload.objects.create()
        if 'inventory_id' in validated_data:
            self.create_acumatica(image_upload, validated_data)
        for index in range(1, 6):
            web_image = validated_data.get(f'web_image_{index}')
            if web_image:
                self.create_web(image_upload, web_image, index)
        return image_upload

    def save(self, **kwargs):
        instance = super().save()
        push_to_acumatica(instance)
        return instance
