from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Link, Collection
from .serializers import LinkSerializer, CollectionSerializer
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .utils import fetch_link_data
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from rest_framework.permissions import IsAuthenticated


User = get_user_model()


class RegisterView(APIView):
    @swagger_auto_schema(
        operation_summary="Регистрация нового пользователя",
        operation_description="Эндпоинт для регистрации нового пользователя. Требуются обязательные поля: username, email, password.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя (уникальное)'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Электронная почта'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль пользователя'),
            },
            required=['username', 'email', 'password']
        ),
        responses={
            201: openapi.Response(description="Пользователь успешно зарегистрирован", examples={
                "application/json": {
                    "message": "Пользователь успешно зарегистрирован."
                }
            }),
            400: openapi.Response(description="Некорректные данные", examples={
                "application/json": {
                    "error": "Пользователь с таким username уже существует."
                }
            }),
        }
    )
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if not username or not email or not password:
            raise ValidationError("Пожалуйста, заполните все поля: username, email, password.")

        if User.objects.filter(username=username).exists():
            raise ValidationError("Пользователь с таким username уже существует.")

        user = User.objects.create_user(username=username, email=email, password=password)
        return Response({"message": "Пользователь успешно зарегистрирован."}, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    @swagger_auto_schema(
        operation_summary="Получить токены (логин пользователя)",
        operation_description="Эндпоинт для аутентификации пользователя. Возвращает `access` и `refresh` токены.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль'),
            },
            required=['username', 'password']
        ),
        responses={
            200: openapi.Response(
                description="Успешный вход",
                examples={
                    "application/json": {
                        "access": "your_access_token",
                        "refresh": "your_refresh_token"
                    }
                }
            ),
            401: openapi.Response(
                description="Неверные учетные данные",
                examples={
                    "application/json": {
                        "detail": "No active account found with the given credentials"
                    }
                }
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Сменить пароль",
        operation_description="Позволяет аутентифицированному пользователю сменить пароль.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description='Старый пароль'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='Новый пароль'),
            },
            required=['old_password', 'new_password']
        ),
        responses={
            200: openapi.Response(description="Пароль успешно изменён."),
            400: openapi.Response(description="Ошибка валидации."),
        }
    )
    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response({"error": "Both old_password and new_password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # Проверяем старый пароль
        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        # Устанавливаем новый пароль
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password successfully changed."}, status=status.HTTP_200_OK)


class PasswordResetView(APIView):
    
    @swagger_auto_schema(
        operation_summary="Запрос на сброс пароля",
        operation_description="Отправляет ссылку для сброса пароля на указанный email.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email пользователя'),
            },
            required=['email']
        ),
        responses={
            200: openapi.Response(description="Ссылка для сброса пароля отправлена."),
            404: openapi.Response(description="Пользователь с указанным email не найден."),
        }
    )
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

        # Генерация токена и ссылки
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = f"http://127.0.0.1:8000/reset-password/{uid}/{token}/"

        # Отправка письма
        send_mail(
            "Password Reset",
            f"Click the link to reset your password: {reset_url}",
            "noreply@example.com",
            [email],
        )

        return Response({"message": "Password reset link sent to your email."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):

    @swagger_auto_schema(
        operation_summary="Подтверждение сброса пароля",
        operation_description="Устанавливает новый пароль для пользователя по токену сброса.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='Новый пароль'),
            },
            required=['new_password']
        ),
        responses={
            200: openapi.Response(description="Пароль успешно сброшен."),
            400: openapi.Response(description="Неверная ссылка или токен."),
        }
    )
    def post(self, request, uidb64, token):
        new_password = request.data.get('new_password')
        if not new_password:
            return Response({"error": "New password is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Invalid link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password successfully reset."}, status=status.HTTP_200_OK)


class LinkView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Получить все ссылки пользователя",
        responses={
            200: openapi.Response('Список ссылок', LinkSerializer(many=True)),
        },
    )
    def get(self, request):
        links = Link.objects.filter(user=request.user)
        serializer = LinkSerializer(links, many=True)
        return Response(serializer.data)


    @swagger_auto_schema(
        operation_summary="Создать новую ссылку",
        operation_description="Добавить ссылку с автоматическим извлечением метаданных (title, description, image)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'url': openapi.Schema(type=openapi.TYPE_STRING, description='Ссылка на ресурс'),
            },
            required=['url']
        ),
        responses={
            201: LinkSerializer,
            400: 'Bad Request',
        },
    )
    def post(self, request):
        url = request.data.get('url')
        if not url:
            return Response({"error": "URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        link_data = fetch_link_data(url)
        link = Link.objects.create(
            user=request.user,
            title=link_data['title'],
            description=link_data['description'],
            url=link_data['url'],
            image=link_data['image'],
            link_type=link_data['link_type']
        )

        return Response({
            "id": link.id,
            "title": link.title,
            "description": link.description,
            "url": link.url,
            "image": link.image,
            "link_type": link.link_type,
            "created_at": link.created_at,
        }, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_summary="Обновить ссылку (полное обновление)",
        operation_description="Полное обновление ссылки. Все поля должны быть переданы в запросе.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='Название ссылки'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Описание ссылки'),
                'url': openapi.Schema(type=openapi.TYPE_STRING, description='URL ссылки'),
            },
            required=['title', 'url']
        ),
        responses={
            200: openapi.Response(description="Ссылка успешно обновлена"),
            400: openapi.Response(description="Ошибка валидации"),
            404: openapi.Response(description="Ссылка не найдена"),
        }
    )
    def put(self, request, pk):
        link = get_object_or_404(Link, pk=pk, user=request.user)
        serializer = LinkSerializer(link, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Обновить ссылку (частичное обновление)",
        operation_description="Частичное обновление ссылки. Можно передать только изменяемые поля.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='Название ссылки'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Описание ссылки'),
                'url': openapi.Schema(type=openapi.TYPE_STRING, description='URL ссылки'),
            },
        ),
        responses={
            200: openapi.Response(description="Ссылка успешно обновлена"),
            400: openapi.Response(description="Ошибка валидации"),
            404: openapi.Response(description="Ссылка не найдена"),
        }
    )
    def patch(self, request, pk):
        link = get_object_or_404(Link, pk=pk, user=request.user)
        serializer = LinkSerializer(link, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Удалить ссылку",
        operation_description="Удаление ссылки пользователя.",
        responses={
            204: openapi.Response(description="Ссылка успешно удалена"),
            404: openapi.Response(description="Ссылка не найдена"),
        }
    )
    def delete(self, request, pk):
        link = get_object_or_404(Link, pk=pk, user=request.user)
        link.delete()
        return Response({"message": "Ссылка успешно удалена."}, status=status.HTTP_204_NO_CONTENT)


class CollectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Получить все коллекции пользователя",
        responses={
            200: openapi.Response('Список коллекций', CollectionSerializer(many=True)),
        },
    )
    def get(self, request):
        collections = Collection.objects.filter(user=request.user)
        serializer = CollectionSerializer(collections, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Создать новую коллекцию",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Название коллекции'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Описание коллекции'),
                'links': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='Список ID ссылок, которые нужно добавить в коллекцию (опционально)'
                ),
            },
            required=['name']
        ),
        responses={
            201: openapi.Response(description="Коллекция успешно создана"),
            400: openapi.Response(description="Ошибка валидации данных"),
        }
    )
    def post(self, request):
        serializer = CollectionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Обновить коллекцию (полное обновление)",
        operation_description="Полное обновление коллекции. Все поля должны быть переданы в запросе.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Название коллекции'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Описание коллекции'),
                'links': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='Список ID ссылок, привязанных к коллекции'
                ),
            },
            required=['name']
        ),
        responses={
            200: openapi.Response(description="Коллекция успешно обновлена"),
            400: openapi.Response(description="Ошибка валидации"),
            404: openapi.Response(description="Коллекция не найдена"),
        }
    )
    def put(self, request, pk):
        collection = get_object_or_404(Collection, pk=pk, user=request.user)
        serializer = CollectionSerializer(collection, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Обновить коллекцию (частичное обновление)",
        operation_description="Частичное обновление коллекции. Можно передать только изменяемые поля.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Название коллекции'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Описание коллекции'),
                'links': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='Список ID ссылок, привязанных к коллекции'
                ),
            },
        ),
        responses={
            200: openapi.Response(description="Коллекция успешно обновлена"),
            400: openapi.Response(description="Ошибка валидации"),
            404: openapi.Response(description="Коллекция не найдена"),
        }
    )
    def patch(self, request, pk):
        collection = get_object_or_404(Collection, pk=pk, user=request.user)
        serializer = CollectionSerializer(collection, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Удалить коллекцию",
        operation_description="Удаление коллекции пользователя.",
        responses={
            204: openapi.Response(description="Коллекция успешно удалена"),
            404: openapi.Response(description="Коллекция не найдена"),
        }
    )
    def delete(self, request, pk):
        collection = get_object_or_404(Collection, pk=pk, user=request.user)
        collection.delete()
        return Response({"message": "Коллекция успешно удалена."}, status=status.HTTP_204_NO_CONTENT)
