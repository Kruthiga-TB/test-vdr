# from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PlanSerializer
from .models import Plan


class PlanCreateView(APIView):

    def post(self, request):
        plan_name = request.data.get("name")

        # 🔥 Check duplicate plan
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

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from .serializers import PlanSerializer

# class PlanCreateView(APIView):
#     def post(self, request):
#         serializer = PlanSerializer(data=request.data)

#         if serializer.is_valid():
#             serializer.save()
#             return Response({'message': 'This plan add.', 'data': serializer.data}, status=status.HTTP_201_CREATED)

#         return Response({'message': 'This plan Not add.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)