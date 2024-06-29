from django.shortcuts import render
from django.http import JsonResponse
from .models import User, Audio
from .serializers import UserSerializer, AudioSerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.contrib.auth import authenticate
from django.contrib.auth.backends import ModelBackend
from .models import CustomTokenAuthentication
from .models import CustomToken as Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from pytube import YouTube
from moviepy.editor import AudioFileClip
from rest_framework import status
from rest_framework.response import Response
import base64
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
from moviepy.editor import VideoFileClip


# Create your views here.

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = User
        print(kwargs)
        print('above here')
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password):
            return user

    def get_user(self, user_id):
        UserModel = User
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None


@api_view(['POST', 'GET', 'DELETE'])
@authentication_classes([])
@permission_classes([])
def sessions(request):
    if request.method == 'POST':
        email = request.data.get('email')
        password = request.data.get('password')
        print(email)
        print(password)
        password = request.data.get('password')
        user = authenticate(username=email.lower(), password=password)
        print(user)
        print(user)
        print(request)
        if user is not None:
            request.session['key'] = 'value'
            print(user)
            token, created = Token.objects.get_or_create(user=user)
            return JsonResponse({'token': token.key})
        else:
            return JsonResponse({'message': 'Invalid credentials'})
        
    elif request.method == 'GET':
        auth_header = request.headers.get('Authorization')
            # Split the header into parts
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'token':
        # Use the second part as the token
            token = parts[1]
        else:
            return JsonResponse({'message': 'Invalid Authorization header format'})
        if token is None:
            return JsonResponse({'message': 'No token provided'})
        try:
            token = Token.objects.get(key=token)
            return JsonResponse({'message': True})
        except Token.DoesNotExist:
            return JsonResponse({'message': False})
        
        
    elif request.method == 'DELETE':
        auth_header = request.headers.get('Authorization')
    # Split the header into parts
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == 'token':
        # Use the second part as the token
        token = parts[1]
    else:
        return JsonResponse({'message': 'Invalid Authorization header format'})

    try:
        token = Token.objects.get(key=token)
        token.delete()
        return JsonResponse({'message': 'Token deleted'})
    except Token.DoesNotExist:
        return JsonResponse({'message': 'Token does not exist'})


@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
@permission_classes([IsAuthenticated])
def userList(request):
    if request.method == 'GET':
        users = User.objects.all()
        serializer = UserSerializer(request.user)
        return JsonResponse(serializer.data, safe=False)

        
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def createUser(request):
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)
    


@api_view(['POST'])
@authentication_classes([CustomTokenAuthentication])
@permission_classes([IsAuthenticated])
def convertVideo(request):
    if request.method == 'POST':
        url = request.data.get('url')
        if not url:
            return Response({'error': 'YouTube URL is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        yt = YouTube(url)
        video = yt.streams.first()  # Download a stream that contains both video and audio
        download_path = video.download(output_path=settings.MEDIA_ROOT)
    
        # Extract frame as image
        video_clip = VideoFileClip(download_path)
        preview_image_path = os.path.splitext(download_path)[0] + '.jpg'
        video_clip.save_frame(preview_image_path, t='00:00:01')  # save frame at 1 second
    
         # Convert to MP3
        audio_clip = video_clip.audio  # Extract the audio from the video
        mp3_path = os.path.splitext(download_path)[0] + '.mp3'
        audio_clip.write_audiofile(mp3_path)
        audio_clip.close()
        video_clip.close()
        # Clean up the original video file  
        os.remove(download_path)
        
        mp3_url = settings.MEDIA_URL + os.path.basename(mp3_path)
        mp3_title = os.path.splitext(os.path.basename(audio_clip.filename))[0]

        # Create a new Audio object
        audio = Audio(user=request.user, name=mp3_title, audio=mp3_path, preview_image=preview_image_path)
        audio.save()
        serializer = AudioSerializer(audio, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
@permission_classes([IsAuthenticated])
def getAllAudio(request):
    if request.method == 'GET':
        audio = Audio.objects.filter(user=request.user)
        serializer = AudioSerializer(audio, many=True, context={'request': request})
        return JsonResponse(serializer.data, safe=False)

@api_view(['DELETE', 'GET', 'PATCH'])
@authentication_classes([CustomTokenAuthentication])
@permission_classes([IsAuthenticated])
def audio(request, id):
    if request.method == 'DELETE':
        try:
            audio = Audio.objects.get(id=id, user=request.user)
            if os.path.isfile(audio.audio.path):
                os.remove(audio.audio.path)
            if os.path.isfile(audio.preview_image.path):
                os.remove(audio.preview_image.path)
            
            audio.delete()
            return JsonResponse({'message': 'Audio deleted'})
        except Audio.DoesNotExist:
            return JsonResponse({'message': 'Audio does not exist'})
        
    if request.method == 'GET':
        try:
            audio = Audio.objects.get(id=id, user=request.user)
            serializer = AudioSerializer(audio, context={'request': request})
            return JsonResponse(serializer.data)
        except Audio.DoesNotExist:
            return JsonResponse({'message': 'Audio does not exist'})
        

    if request.method == 'PATCH':
        try:
            audio = Audio.objects.get(id=id, user=request.user)
            new_name = request.data.get('name', audio.name)
            if new_name != audio.name:
                # Get the old file path
                old_file = audio.audio.path

                # Create a new file path
                new_file = os.path.join(os.path.dirname(old_file), f'{new_name}.mp3')

                # Move the old file to the new file path
                if default_storage.exists(old_file):
                    default_storage.save(new_file, default_storage.open(old_file))
                    default_storage.delete(old_file)

                # Update the audio object
                audio.audio.name = os.path.basename(new_file)
                audio.name = new_name

            data_url = request.data.get('image')
            if data_url:
                # Delete the old preview image
                if audio.preview_image and os.path.isfile(audio.preview_image.path):
                    os.remove(audio.preview_image.path)

                # Convert the data URL to an image file
                format, imgstr = data_url.split(';base64,') 
                ext = format.split('/')[-1] 
                data = ContentFile(base64.b64decode(imgstr), name=f'{audio.name}_preview.{ext}') 

                # Save the new image to the 'preview_image' field
                audio.preview_image.save(data.name, data)

            audio.save()
            serializer = AudioSerializer(audio, context={'request': request})
            return JsonResponse(serializer.data)
        except Audio.DoesNotExist:
            return JsonResponse({'message': 'Audio does not exist'})

    return JsonResponse({'message': 'Invalid request method'})

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
@permission_classes([IsAuthenticated])
def getAudioByName(request, name):
    if request.method == 'GET':
        try:
            audio = Audio.objects.get(name=name, user=request.user)
            serializer = AudioSerializer(audio, context={'request': request})
            return JsonResponse(serializer.data)
        except Audio.DoesNotExist:
            return JsonResponse({'message': 'Audio does not exist'})
            
        return JsonResponse({'message': 'Invalid request method'})
    