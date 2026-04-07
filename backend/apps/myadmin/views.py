# from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Plan
from .serializers import PlanSerializer

# class PlanListView(APIView):
#     def get(self, request):
#         plans = Plan.objects.all()
#         serializer = PlanSerializer(plans, many=True)
#         return Response(serializer.data)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PlanSerializer

class PlanCreateView(APIView):
    def post(self, request):
        serializer = PlanSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'This plan add.', 'data': serializer.data}, status=status.HTTP_201_CREATED)

        return Response({'message': 'This plan Not add.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)