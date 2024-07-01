from django.urls import path
from .views import home,handle_user_choice,handle_bot_style,createbot,chat_with_bot

urlpatterns = [

    path('v1/home/<int:botid>', home, name='home'),
    path('v1/handle_user_choice/<int:botid>', handle_user_choice, name='handle_user_choice'),
    path('v1/botstyle/<int:botid>', handle_bot_style, name='handle_bot_style'),
    path('v1/createbot/<int:botid>', createbot, name='createbot'),
    path('v1/chat/<int:botid>', chat_with_bot, name='chat_with_bot'),

]
