import os
from wsgiref.util import FileWrapper
import re
from django.http import HttpResponse
from pydub.utils import mediainfo
from django.http import StreamingHttpResponse
import logging

logger = logging.getLogger(__name__)

class RangeFileWrapper(FileWrapper):
    def __init__(self, *args, **kwargs):
        self.start, self.end = kwargs.pop('start', None), kwargs.pop('end', None)
        super().__init__(*args, **kwargs)

    def __iter__(self):
        self.filelike.seek(self.start)
        while True:
            data = self.filelike.read(self.blksize)
            if not data or (self.end and self.filelike.tell() > self.end):
                break
            yield data

class ByteRangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        http_range = request.META.get('HTTP_RANGE')
        if http_range and response.status_code == 200:
            # Calculate the duration of the audio file in minutes
            audio_info = mediainfo(response.file_to_stream.name)
            duration = float(audio_info['duration']) / 60

            logger.info(f"Duration of the file: {duration} minutes")

            # Only process the file if it's shorter than 6 minutes
            if duration <= 1:
                byte1, byte2 = 0, None
                m = re.search('(\d+)-(\d*)', http_range)
                if m:
                    byte1, byte2 = m.groups()

                byte1, byte2 = int(byte1), int(byte2) if byte2 else None

                logger.info(f"Requested byte range: {byte1}-{byte2}")

                length = os.path.getsize(response.file_to_stream.name)
                byte2 = byte2 or length - 1

                if byte1 < 0 or byte2 >= length or byte1 > byte2:
                    return HttpResponse(status=416)

                response = StreamingHttpResponse(
                    RangeFileWrapper(response.file_to_stream, blksize=8192, start=byte1, end=byte2),
                    status=206,
                    content_type=response['Content-Type']
                )
                response['Content-Range'] = 'bytes %s-%s/%s' % (byte1, byte2, length)
                response['Accept-Ranges'] = 'bytes'

        return response
