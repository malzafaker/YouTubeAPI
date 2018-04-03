import http.client as httplib
import httplib2
import logging
import random
import time

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import GenericViewSet

from apps.accounts.permissions import IsAdministratorUserOrCurrentUser

from apps.youtube.models import YouTubeVideo
from apps.youtube.serializers import YouTubeVideoSerializer
from apps.youtube.youtube import get_authenticated_service


logger = logging.getLogger(__name__)

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
  httplib.IncompleteRead, httplib.ImproperConnectionState,
  httplib.CannotSendRequest, httplib.CannotSendHeader,
  httplib.ResponseNotReady, httplib.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]


def initialize_upload(youtube, data):
    logger.info('Initialize_upload', exc_info=True)

    title = data.get('title', '')
    description = data.get('description', '')
    body = dict(
        snippet=dict(
          title=title,
          description=description,
          tags=[],
          categoryId='27'
        ),
        status=dict(
          privacyStatus='unlisted'
        )
    )
    file = data['file']
    logger.info('youtube %s' % youtube, exc_info=True)
    insert_request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting 'chunksize' equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=MediaFileUpload(file.temporary_file_path(), chunksize=-1, resumable=True)
    )

    response = None
    error = None
    retry = 0
    data = {
        'success': True,
        'errors': ''
    }
    while response is None:
        try:
            logger.info('Uploading file...', exc_info=True)
            status, response = insert_request.next_chunk()
            if response is not None:
                logger.info('Response:%s' % response, exc_info=True)
                # http://www.youtube.com/watch?v=
                if 'id' in response:
                    video_id = response['id']
                    logger.info('Video id "%s" was successfully uploaded.' % video_id, exc_info=True)
                    youtube_url = 'http://www.youtube.com/watch?v=%s ' % video_id
                    data['video_id'] = video_id
                    data['youtube_url'] = youtube_url
                    YouTubeVideo.objects.create(
                        video_id=video_id,
                        title=title,
                        description=description,
                        youtube_url=youtube_url,
                    )
                    return data
                else:
                    logger.error('The upload failed with an unexpected response: %s' % response, exc_info=True)
                    data['errors'] = 'The upload failed with an unexpected response: %s' % response
                    return data
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                logger.error('A retriable HTTP error %d occurred:\n%s' % (e.resp.status, e.content), exc_info=True)
                data['errors'] = 'A retriable HTTP error %d occurred:\n%s' % (e.resp.status, e.content)
                return data
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = 'A retriable error occurred: %s' % e
            logger.error(error, exc_info=True)
            data['errors'] = error
            return data

        if error is not None:
            logger.error(error, exc_info=True)
            retry += 1
            if retry > MAX_RETRIES:
                data['errors'] = 'No longer attempting to retry.'
                return data
            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            logger.info('Sleeping %f seconds and then retrying...' % sleep_seconds, exc_info=True)
            time.sleep(sleep_seconds)
        return data


class YouTubeViewSet(GenericViewSet):
    http_method_names = ['get', 'post', 'head']
    queryset = YouTubeVideo
    permission_classes = [IsAdministratorUserOrCurrentUser]
    serializers = {
        'default':  YouTubeVideoSerializer
    }

    def get_serializer_class(self):
        return self.serializers.get(self.action,
                                    self.serializers['default'])

    @list_route(methods=["POST"])
    def upload(self, request, *args, **kwargs):
        """ Загрузка видео"""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        youtube = get_authenticated_service(request)
        data = initialize_upload(youtube, request.data)
        if data['errors']:
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(data, status=status.HTTP_201_CREATED)

    @list_route(methods=["get"], url_path='remove/(?P<pk>[-a-zA-Z0-9_]+)')
    def remove(self, request, *args, **kwargs):
        """ Удалить видео """
        instance = YouTubeVideo.objects.filter(video_id=kwargs['pk']).first()
        if not instance:
            return Response(data={"detail": "Не найдено."}, status=status.HTTP_404_NOT_FOUND)
        youtube = get_authenticated_service(request)
        instance.delete()
        data = self.video_delete(youtube, id=kwargs['pk'])
        return Response(data=data, status=status.HTTP_204_NO_CONTENT)

    def video_delete(self, client, **kwargs):
        response = client.videos().delete(
            **kwargs
        ).execute()
        return {
            'success': True,
            'errors': ''
        }
