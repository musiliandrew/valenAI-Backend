import os
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Valentine
from .mpesa import MpesaClient
from .serializers import (
    ValentineCreateSerializer,
    ValentineDetailSerializer,
    ValentineListSerializer,
    ValentineResponseSerializer,
    ValentineManagementSerializer
)


class ValentineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Valentine operations:
    - Create: POST /api/valentines/
    - Retrieve by slug: GET /api/valentines/{slug}/
    - List recent (Wall of Lovers): GET /api/valentines/wall/
    - Mark accepted: POST /api/valentines/{slug}/respond/
    """
    
    queryset = Valentine.objects.all()
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ValentineCreateSerializer
        elif self.action == 'wall':
            return ValentineListSerializer
        return ValentineDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new Valentine and return the unique link"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        valentine = serializer.save()
        
        # Return the created Valentine with slug and secret management token
        return Response({
            'success': True,
            'message': 'Valentine created successfully!',
            'data': {
                'slug': valentine.slug,
                'management_token': valentine.management_token,
                'recipient_name': valentine.recipient_name,
            },
            'link': f"/d/{valentine.slug}",
            'manage_link': f"/manage/{valentine.management_token}"
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve Valentine metadata or full data if unlocked"""
        valentine = self.get_object()
        
        # Check if paid or if creator is previewing
        mgmt_token = request.query_params.get('token')
        is_owner = mgmt_token == valentine.management_token
        
        if not valentine.is_paid and not is_owner:
            return Response({
                'success': False,
                'message': 'This Valentine has not been published yet.',
                'is_paid': False
            }, status=status.HTTP_402_PAYMENT_REQUIRED)

        valentine.increment_views()
        serializer = self.get_serializer(valentine)
        data = serializer.data
        data['is_paid'] = valentine.is_paid
        
        if valentine.protection_answer:
            # Hide sensitive fields on initial GET
            data['is_locked'] = True
            data['message'] = "Locked by secret question"
            data['music_link'] = None
            data['image_url'] = None
            data['image'] = None
        else:
            data['is_locked'] = False
            
        return Response(data)

    @action(detail=True, methods=['post'])
    def unlock(self, request, slug=None):
        """
        Verify the answer to the secret question and return full data
        POST /api/valentines/{slug}/unlock/
        """
        valentine = self.get_object()
        provided_answer = request.data.get('answer', '').strip().lower()
        correct_answer = (valentine.protection_answer or '').strip().lower()
        
        if provided_answer == correct_answer:
            serializer = self.get_serializer(valentine)
            data = serializer.data
            data['is_locked'] = False # Explicitly unlock
            return Response({
                'success': True,
                'message': 'Unlocked! ❤️',
                'data': data
            })
        else:
            return Response({
                'success': False,
                'message': "Nope, that's not it! Try again? 😉"
            }, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=False, methods=['get'])
    def wall(self, request):
        """
        Get recent Valentines for the Wall of Lovers
        GET /api/valentines/wall/?limit=10
        """
        limit = int(request.query_params.get('limit', 10))
        valentines = self.queryset[:limit]
        serializer = self.get_serializer(valentines, many=True)
        return Response({
            'success': True,
            'count': len(serializer.data),
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def respond(self, request, slug=None):
        """
        Mark Valentine as accepted/rejected
        POST /api/valentines/{slug}/respond/
        Body: { "accepted": true }
        """
        valentine = self.get_object()
        serializer = ValentineResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check protection if enabled
        if valentine.protection_answer:
            provided_answer = serializer.validated_data.get('protection_answer', '').strip().lower()
            correct_answer = valentine.protection_answer.strip().lower()
            
            if provided_answer != correct_answer:
                return Response({
                    'success': False,
                    'message': "Oops! That's not the right answer. Your partner set a secret question!",
                    'needs_protection': True
                }, status=status.HTTP_403_FORBIDDEN)

        if serializer.validated_data['accepted']:
            valentine.mark_accepted()
            message = f"{valentine.recipient_name} said YES! 🎉"
        else:
            message = "Response recorded"
        
        return Response({
            'success': True,
            'message': message,
            'is_accepted': valentine.is_accepted
        })

    @action(detail=False, methods=['get'], url_path='manage/(?P<token>[^/.]+)')
    def manage(self, request, token=None):
        """
        Manage a Valentine using a management token
        GET /api/valentines/manage/{token}/
        """
        valentine = get_object_or_404(Valentine, management_token=token)
        serializer = ValentineManagementSerializer(valentine)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get platform statistics
        GET /api/valentines/stats/
        """
        total_valentines = Valentine.objects.count()
        total_accepted = Valentine.objects.filter(is_accepted=True).count()
        total_views = sum(Valentine.objects.values_list('views_count', flat=True))
        
        return Response({
            'success': True,
            'stats': {
                'total_valentines': total_valentines,
                'total_accepted': total_accepted,
                'total_views': total_views,
                'acceptance_rate': round((total_accepted / total_valentines * 100) if total_valentines > 0 else 0, 2)
            }
        })

    @action(detail=False, methods=['get'])
    def search_music(self, request):
        """
        Search for tracks on Spotify
        GET /api/valentines/search_music/?q=perfect
        """
        import requests
        import base64
        import logging
        from django.conf import settings

        logger = logging.getLogger(__name__)
        
        query = request.query_params.get('q')
        if not query:
            return Response({'error': 'No search query provided'}, status=400)
            
        client_id = settings.SPOTIFY_CLIENT_ID
        client_secret = settings.SPOTIFY_CLIENT_SECRET
        
        if not client_id or not client_secret:
            logger.error("Spotify credentials missing in settings")
            return Response({'error': 'Spotify credentials not configured'}, status=500)
            
        try:
            # Get Spotify Access Token
            auth_url = 'https://accounts.spotify.com/api/token'
            auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
            
            auth_response = requests.post(auth_url, data={
                'grant_type': 'client_credentials'
            }, headers={
                'Authorization': f'Basic {auth_header}'
            }, timeout=5)
            
            if auth_response.status_code != 200:
                logger.error(f"Spotify Auth Failed: {auth_response.status_code} - {auth_response.text}")
                return Response({'error': 'Failed to authenticate with Spotify', 'details': auth_response.text}, status=status.HTTP_502_BAD_GATEWAY)
                
            access_token = auth_response.json().get('access_token')
            
            # Search for Tracks
            search_url = 'https://api.spotify.com/v1/search'
            search_response = requests.get(search_url, params={
                'q': query,
                'type': 'track',
                'limit': 10,
                'market': 'US'
            }, headers={
                'Authorization': f'Bearer {access_token}'
            }, timeout=5)
            
            if search_response.status_code != 200:
                logger.error(f"Spotify Search Failed: {search_response.status_code} - {search_response.text}")
                return Response({
                    'error': 'Search failed',
                    'status_code': search_response.status_code,
                    'details': search_response.json() if 'application/json' in search_response.headers.get('Content-Type', '') else search_response.text
                }, status=status.HTTP_502_BAD_GATEWAY)
                
            tracks = search_response.json().get('tracks', {}).get('items', [])
            results = [{
                'id': track['id'],
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'external_url': track['external_urls']['spotify'],
                'uri': track['uri']
            } for track in tracks]
            
            return Response({'success': True, 'data': results})
        except requests.exceptions.RequestException as e:
            logger.exception("Music search failed due to network error")
            return Response({'error': 'Network error while searching music', 'details': str(e)}, status=500)
        except Exception as e:
            logger.exception("Unexpected error in search_music")
            return Response({'error': 'An unexpected error occurred', 'details': str(e)}, status=500)

    @action(detail=False, methods=['post'])
    def generate_message(self, request):
        """
        Generate romantic messages using AI
        POST /api/valentines/generate_message/
        """
        from .ai_service import generate_romantic_message
        
        sender_name = request.data.get('sender_name')
        recipient_name = request.data.get('recipient_name')
        
        if not sender_name or not recipient_name:
            return Response(
                {'success': False, 'message': 'Sender and recipient names are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        messages = generate_romantic_message(
            sender_name=sender_name,
            receiver_name=recipient_name,
            tone=request.data.get('tone', 'romantic'),
            length=request.data.get('length', 'medium'),
            context=request.data.get('context', '')
        )
        
        return Response({
            'success': True,
            'messages': messages
        })

    @action(detail=False, methods=['post'])
    def generate_poem(self, request):
        """
        Generate romantic poems using AI
        POST /api/valentines/generate_poem/
        """
        from .ai_service import generate_poem
        
        sender_name = request.data.get('sender_name')
        recipient_name = request.data.get('recipient_name')
        
        if not sender_name or not recipient_name:
            return Response(
                {'success': False, 'message': 'Sender and recipient names are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        poems = generate_poem(
            sender_name=sender_name,
            receiver_name=recipient_name,
            vibe=request.data.get('vibe', 'romantic'),
            context=request.data.get('context', '')
        )
        
        return Response({
            'success': True,
            'poems': poems
        })

    @action(detail=True, methods=['post'])
    def submit_manual_payment(self, request, slug=None):
        """
        Submit a manual M-Pesa transaction code
        POST /api/valentines/{slug}/submit_manual_payment/
        """
        valentine = self.get_object()
        mpesa_code = request.data.get('code', '').strip().upper()
        
        if not mpesa_code:
            return Response({'success': False, 'message': 'M-Pesa confirmation code is required'}, status=400)
            
        if len(mpesa_code) < 8:
            return Response({'success': False, 'message': 'Please enter a valid M-Pesa code (e.g., SBN8SDF92)'}, status=400)

        # Check for duplicates
        if Valentine.objects.filter(mpesa_code=mpesa_code).exclude(pk=valentine.pk).exists():
             return Response({'success': False, 'message': 'This code has already been used.'}, status=400)

        valentine.mpesa_code = mpesa_code
        valentine.is_paid = True # Mark as paid immediately for viral growth, but store the code
        valentine.is_pending_verification = True # Mark for admin review
        valentine.save()
        
        return Response({
            'success': True,
            'message': 'Payment confirmed! Your Valentine is now live. ❤️',
            'data': {
                'is_paid': valentine.is_paid,
                'slug': valentine.slug
            }
        })

    @action(detail=True, methods=['post'])
    def reveal_manual_payment(self, request, slug=None):
        """
        Submit code to reveal answer
        POST /api/valentines/{slug}/reveal_manual_payment/
        """
        valentine = self.get_object()
        mpesa_code = request.data.get('code', '').strip().upper()
        
        if not mpesa_code:
            return Response({'success': False, 'message': 'M-Pesa code required'}, status=400)
            
        # For reveal, we can just return the answer once they provide ANY code
        # In a real app, you'd verify it first.
        valentine.mpesa_code = mpesa_code
        valentine.save()
        
        return Response({
            'success': True,
            'message': 'Code received! Here is your secret answer:',
            'answer': valentine.protection_answer or "No secret set!"
        })
