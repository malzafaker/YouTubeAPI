# -*- coding: utf-8 -*-
import requests
import logging

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

from django.conf import settings
from django.shortcuts import redirect

CLIENT_SECRETS_FILE = settings.BASE_DIR + '/settings/parts/you_tube_client_secrets.json'

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

logger = logging.getLogger(__name__)
SITE_HOST = settings.SITE_HOST


def get_authenticated_service(request):
    logger.info('get_authenticated_service...', exc_info=True)
    if 'credentials' not in request.session:
        logger.info('redirect to authorize', exc_info=True)
        return redirect('/api/v1/oauth_youtube/authorize/')
    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(**request.session['credentials'])
    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    request.session['credentials'] = credentials_to_dict(credentials)
    return youtube


def authorize(request):
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)

    # flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    flow.redirect_uri = '{site_host}/api/v1/oauth_youtube/oauth2callback/'.format(
        site_host=SITE_HOST
    )

    authorization_url, state = flow.authorization_url(
      access_type='offline',
      include_granted_scopes='true')
    request.session['state'] = state
    return redirect(authorization_url)


def oauth2callback(request):
    logger.info('oauth2callback', exc_info=True)
    state = request.session.get('state', '')

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)

    flow.redirect_uri = '{site_host}/api/v1/oauth_youtube/oauth2callback/'.format(
        site_host=SITE_HOST
    )

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = '{site_host}{path}'.format(
        site_host=SITE_HOST,
        path=request.get_full_path(),
    )
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)
    logger.info('%s' % request.session['credentials'], exc_info=True)
    return redirect('/')


def revoke(request):
    if 'credentials' not in request.session:
        logger.error('You need to <a href="/authorize">authorize</a> before testing the code to revoke credentials.', exc_info=True)

    credentials = google.oauth2.credentials.Credentials(**request.session['credentials'])

    revoke = requests.post('https://accounts.google.com/o/oauth_youtube/revoke',
                           params={'token': credentials.token},
                           headers={'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        logger.info('status_code 200', exc_info=True)
    else:
        logger.error('An error occurred.', exc_info=True)


def clear_credentials(request):
    if 'credentials' in request.session:
        del request.session['credentials']


def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
