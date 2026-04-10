from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PlanSerializer
from .models import Plan
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi
# from rest_framework.generics import GenericAPIView
# from rest_framework import generics
# from rest_framework.generics import CreateAPIView


class PlanCreate(APIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def post(self, request):
        plan_name = request.data.get("name")

        if Plan.objects.filter(name=plan_name).exists():
            return Response(
                {"message": "Plan already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PlanSerializer(data=request.data)

        if serializer.is_valid():
            plan = serializer.save()

            return Response(
                {
                    "message": "Plan created successfully",
                    "data": PlanSerializer(plan).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                "message": "Plan not created",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )




class PlanCreateView(APIView):
    def get(self, request):
        plans = Plan.objects.all()
        serializer = PlanSerializer(plans, many=True)

        return Response(
            {
                "message": "Plans fetched successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        
        )
        

    

