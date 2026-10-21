from django.urls import path,include
from rest_framework.views import APIView
from rest_framework.response import Response
class Protected(APIView):
 calls=0
 def get(self,request):
  type(self).calls+=1
  return Response({'user_id':str(request.user.pk)})
 def post(self,request): return self.get(request)
from django.contrib import admin
urlpatterns=[path('admin/',admin.site.urls),path('probe/',Protected.as_view()),path('api/auth/',include('apps.users.urls')),
 path('api/products/',include('apps.products.urls')),path('api/organizations/',include('apps.organizations.urls')),path('api/subscriptions/',include('apps.subscriptions.urls')),path('api/billing/',include('apps.billing.urls')),path('api/integration/',include('apps.integration.urls')),path('api/',include('apps.api.urls'))]
