from django.shortcuts import render
from rest_framework.views import APIView
# Create your views here.
from rest_framework import status
from . models import Users
from rest_framework.response import Response



class CheckEmail(APIView):

    def post(self, request):
        response = {"status": "success", "errorcode": "", "reason": "", "result":"", "httpstatus": status.HTTP_200_OK}
        print("=====================")
        return Response(response, status=status.HTTP_200_OK)