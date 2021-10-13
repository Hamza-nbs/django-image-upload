from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .serializers import ImageUploadSerializer
from django.http import HttpResponse
import logging

logger = logging.getLogger('image-uploader')


class FileView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        logger.info('Successfully got following form data:\n%s' % request.data)
        images_serializer = ImageUploadSerializer(data=request.data)
        if images_serializer.is_valid():
            images_serializer.save()
            logger.info('Successfully uploaded with following data:\n%s' % images_serializer.data)
            return Response(images_serializer.data, status=status.HTTP_201_CREATED)
        else:
            logger.error('Uploading failed with following errors:\n%s' % images_serializer.errors)
            return Response(images_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def test_view(request):
    return HttpResponse("<b> Test </b>")
