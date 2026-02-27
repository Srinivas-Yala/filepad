from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import hashlib

from .models import UserSpace, UploadedFile
from .serializers import UploadedFileSerializer, UserSpaceSerializer


def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


@csrf_exempt
@api_view(['POST'])
def authenticate_user(request):
    """Authenticate user with password"""
    password = request.data.get('password')
    
    if not password:
        return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user_hash = hash_password(password)
    user_space, created = UserSpace.objects.get_or_create(user_hash=user_hash)
    serializer = UserSpaceSerializer(user_space, context={'request': request})
    
    return Response({
        'success': True,
        'user_hash': user_hash[:10] + '***',
        'is_new_user': created,
        'data': serializer.data
    })


@csrf_exempt
@api_view(['GET'])
def get_files(request):
    """Get all files for a user"""
    password = request.GET.get('password')
    
    if not password:
        return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user_hash = hash_password(password)
    
    try:
        user_space = UserSpace.objects.get(user_hash=user_hash)
        files = user_space.files.all()
        serializer = UploadedFileSerializer(files, many=True, context={'request': request})
        return Response({'success': True, 'files': serializer.data})
    except UserSpace.DoesNotExist:
        return Response({'success': True, 'files': []})


@csrf_exempt
@api_view(['POST'])
def upload_file(request):
    """Upload a file"""
    password = request.data.get('password')
    uploaded_file = request.FILES.get('file')
    
    if not password or not uploaded_file:
        return Response({'error': 'Password and file required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if uploaded_file.size > 10 * 1024 * 1024:
        return Response({'error': 'File size cannot exceed 10MB'}, status=status.HTTP_400_BAD_REQUEST)
    
    user_hash = hash_password(password)
    user_space, created = UserSpace.objects.get_or_create(user_hash=user_hash)
    
    file_obj = UploadedFile.objects.create(
        user_space=user_space,
        file=uploaded_file,
        original_filename=uploaded_file.name,
        file_size=uploaded_file.size,
        file_type=uploaded_file.content_type or ''
    )
    
    serializer = UploadedFileSerializer(file_obj, context={'request': request})
    return Response({
        'success': True,
        'message': 'File uploaded successfully',
        'file': serializer.data
    }, status=status.HTTP_201_CREATED)


@csrf_exempt
@api_view(['DELETE'])
def delete_file(request, file_id):
    """Delete a file"""
    password = request.data.get('password') or request.GET.get('password')
    
    if not password:
        return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user_hash = hash_password(password)
    
    try:
        user_space = UserSpace.objects.get(user_hash=user_hash)
        file_obj = get_object_or_404(UploadedFile, id=file_id, user_space=user_space)
        file_obj.delete()
        return Response({'success': True, 'message': 'File deleted successfully'})
    except UserSpace.DoesNotExist:
        return Response({'error': 'User space not found'}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(['GET'])
def download_file(request, file_id):
    """Download a file"""
    password = request.GET.get('password')
    
    if not password:
        return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user_hash = hash_password(password)
    
    try:
        user_space = UserSpace.objects.get(user_hash=user_hash)
        file_obj = get_object_or_404(UploadedFile, id=file_id, user_space=user_space)
        
        # Redirect to S3 signed URL or local file
        if hasattr(file_obj.file, 'url'):
            return HttpResponseRedirect(file_obj.file.url)
        
        raise Http404("File not found")
    except UserSpace.DoesNotExist:
        return Response({'error': 'User space not found'}, status=status.HTTP_404_NOT_FOUND)
