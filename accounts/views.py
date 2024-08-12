from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializer import AuthenticationSerializer, SignupSerializer
from accounts.utils import get_tokens_for_user


class SignupView(APIView):
    """
    A Logic for user Sign-up.
    """

    permission_classes = (AllowAny,)
    serializer_class = SignupSerializer

    def post(self, request) -> Response:
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():

            user = get_user_model().objects.create_user(
                username=serializer.validated_data["username"],
                email=serializer.validated_data.get("email", ""),
                password=serializer.validated_data["password"],
            )

            content = {
                "detail": "Signup successful.",
                "user": {"id": user.id, "username": user.username, "email": user.email},
            }

            return Response(content, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """A logic for user Login"""

    permission_classes = (AllowAny,)
    serializer_class = AuthenticationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            username = serializer.data.get("username")
            password = serializer.data.get("password")

            user = authenticate(username=username, password=password)
            if not user:
                content = {"detail": "Invalid credentials."}
                return Response(content, status=status.HTTP_401_UNAUTHORIZED)

            tokens = get_tokens_for_user(user)

            content = {
                "detail": "User verified, login successful.",
                "user": {"id": user.id, "username": user.username, "email": user.email},
            }

            content.update(tokens)
            return Response(content, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
