from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class AuthenticationSerializer(serializers.Serializer):
    """Serializer to validate /signup/ requests"""

    username = serializers.CharField(max_length=50, required=True)
    password = serializers.CharField(required=True)


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with that username already exists."
            )
        return value
