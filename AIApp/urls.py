from django.urls import path
from .views import home,handle_user_choice,handle_bot_style,createbot,chat_with_bot,isbotcreated

urlpatterns = [

    path('v1/home/<str:botid>', home, name='home'),
    path('v1/handle_user_choice/<str:botid>', handle_user_choice, name='handle_user_choice'),
    path('v1/botstyle/<str:botid>', handle_bot_style, name='handle_bot_style'),
    path('v1/createbot/<str:botid>', createbot, name='createbot'),
    path('v1/chat/<str:botid>', chat_with_bot, name='chat_with_bot'),
    path('v1/isbotcreated/<str:botid>', isbotcreated, name='isbotcreated'),

]
