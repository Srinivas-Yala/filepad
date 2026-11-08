
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.utils.http import content_disposition_header

import hashlib
import hmac
import uuid

from .models import UserSpace, UploadedFile
from .serializers import UploadedFileSerializer, UserSpaceSerializer


# CSRF PROTECTION

def enforce_api_csrf(view_func):
    """
    Enforce Django CSRF validation on a DRF function-based API view.
    """
    view_func.csrf_exempt = False
    return csrf_protect(view_func)


# VAULT AUTHENTICATION HELPERS

def get_vault_lookup_id(password):
    """
    Generate a deterministic, secret-keyed vault lookup identifier.
    """
    return hmac.new(
        settings.VAULT_LOOKUP_SECRET.encode('utf-8'),
        password.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def get_authenticated_user_space(request):
    """
    Retrieve the authenticated vault using its UUID in the session.
    """
    vault_uuid = request.session.get('vault_uuid')

    if not vault_uuid:
        return None

    try:
        parsed_uuid = uuid.UUID(vault_uuid)
        return UserSpace.objects.get(vault_uuid=parsed_uuid)

    except (
        ValueError,
        TypeError,
        AttributeError,
        UserSpace.DoesNotExist
    ):
        return None


# AUTHENTICATION

@enforce_api_csrf
@api_view(['POST'])
def authenticate_user(request):
    """
    Create or access a vault using its password.
    """

    password = request.data.get('password')

    if not isinstance(password, str) or not 4 <= len(password) <= 32:
        return Response(
            {'error': 'Vault key must be between 4 and 32 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )

    lookup_id = get_vault_lookup_id(password)

    user_space, created = UserSpace.objects.get_or_create(
        lookup_id=lookup_id,
        defaults={
            'password_verifier': make_password(password)
        }
    )

    if not created:
        if not user_space.password_verifier or not check_password(
            password,
            user_space.password_verifier
        ):
            return Response(
                {'error': 'Invalid vault key'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    request.session.cycle_key()
    request.session['vault_uuid'] = str(user_space.vault_uuid)
    request.session.set_expiry(1800)

    serializer = UserSpaceSerializer(
        user_space,
        context={'request': request}
    )

    return Response({
        'success': True,
        'is_new_user': created,
        'data': serializer.data
    })


# LIST FILES

@api_view(['GET'])
def get_files(request):
    """
    List files belonging to the logged-in vault.
    """

    user_space = get_authenticated_user_space(request)

    if not user_space:
        return Response(
            {'error': 'Please log in'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    files = user_space.files.all()

    serializer = UploadedFileSerializer(
        files,
        many=True,
        context={'request': request}
    )

    return Response({
        'success': True,
        'files': serializer.data
    })


# LOGOUT

@enforce_api_csrf
@api_view(['POST'])
def logout_user(request):
    """
    Destroy the current session.
    """

    request.session.flush()

    return Response({
        'success': True,
        'message': 'Logged out successfully'
    })


# UPLOAD FILE

@enforce_api_csrf
@api_view(['POST'])
def upload_file(request):
    """
    Upload a file using the authenticated session.
    """

    user_space = get_authenticated_user_space(request)
    uploaded_file = request.FILES.get('file')

    if not user_space:
        return Response(
            {'error': 'Please log in'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not uploaded_file:
        return Response(
            {'error': 'File is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if uploaded_file.size > 100 * 1024 * 1024:
        return Response(
            {'error': 'File size cannot exceed 100MB'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if user_space.files.count() >= 5:
        return Response(
            {
                'error': (
                    'Storage limit reached. '
                    'Delete a file before uploading.'
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    file_obj = UploadedFile.objects.create(
        user_space=user_space,
        file=uploaded_file,
        original_filename=uploaded_file.name,
        file_size=uploaded_file.size,
        file_type=uploaded_file.content_type or ''
    )

    serializer = UploadedFileSerializer(
        file_obj,
        context={'request': request}
    )

    return Response(
        {
            'success': True,
            'message': 'File uploaded successfully',
            'file': serializer.data
        },
        status=status.HTTP_201_CREATED
    )


# DELETE FILE

@enforce_api_csrf
@api_view(['DELETE'])
def delete_file(request, file_id):
    """
    Delete a file belonging to the logged-in vault.
    """

    user_space = get_authenticated_user_space(request)

    if not user_space:
        return Response(
            {'error': 'Please log in'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        file_obj = UploadedFile.objects.get(
            id=file_id,
            user_space=user_space
        )

    except UploadedFile.DoesNotExist:
        return Response(
            {'error': 'File not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    file_obj.delete()

    return Response({
        'success': True,
        'message': 'File deleted successfully'
    })


# DOWNLOAD FILE

@api_view(['GET'])
def download_file(request, file_id):
    """
    Download a file belonging to the logged-in vault.
    """

    user_space = get_authenticated_user_space(request)

    if not user_space:
        return Response(
            {'error': 'Please log in'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        file_obj = UploadedFile.objects.get(
            id=file_id,
            user_space=user_space
        )

    except UploadedFile.DoesNotExist:
        return Response(
            {'error': 'File not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if settings.USE_S3:
        import boto3
        from botocore.config import Config

        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME,
            endpoint_url=(
                f"https://s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com"
            ),
            config=Config(signature_version='s3v4')
        )

        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': file_obj.file.name,
                'ResponseContentDisposition': content_disposition_header(
                    True,
                    file_obj.original_filename
                ),
            },
            ExpiresIn=300
        )

        return HttpResponseRedirect(presigned_url)

    return HttpResponseRedirect(file_obj.file.url)
